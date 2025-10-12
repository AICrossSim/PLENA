import cocotb
from cocotb.triggers import *
from cocotb.clock import Clock
from cocotb.utils import get_sim_time


class Testbench:
    __test__ = False  # so pytest doesn't confuse this with a test

    def __init__(
        self,
        dut,
        clk=None,
        rst=None,
        fail_on_checks=True,
        clk_period_ns=20,
    ) -> None:
        self.dut = dut
        self.clk = clk
        self.rst = rst

        self.input_drivers = {}
        self.output_monitors = {}

        self.input_precision = [32]

        self.fail_on_checks = fail_on_checks

        if self.clk is not None:
            self.clock = Clock(self.clk, clk_period_ns, units="ns")
            cocotb.start_soon(self.clock.start())

    def assign_self_params(self, attrs):
        for att in attrs:
            setattr(self, att, int(getattr(self.dut, att).value))

    def get_parameter(self, parameter_name):
        parameter = getattr(self.dut, parameter_name)
        return int(parameter)

    def get_parameter(self, parameter_name):
        parameter = getattr(self.dut, parameter_name)
        return int(parameter)

    async def reset(self, active_high=True):
        if self.rst is None:
            raise Exception(
                "Cannot reset. Either a reset wire was not provided or "
                + "the module does not have a reset."
            )

        await RisingEdge(self.clk)
        self.rst.value = 1 if active_high else 0
        await RisingEdge(self.clk)
        self.rst.value = 0 if active_high else 1
        await RisingEdge(self.clk)

    async def initialize(self):
        await self.reset()

        # Set all monitors ready
        for monitor in self.output_monitors.values():
            monitor.ready.value = 1

    def generate_inputs(self, batches=1):
        raise NotImplementedError

    def load_drivers(self, in_tensors):
        raise NotImplementedError

    def load_monitors(self, expectation):
        raise NotImplementedError

    async def wait_end(self, timeout=1, timeout_unit="ms"):
        while True:
            await RisingEdge(self.clk)

            # ! TODO: check if this slows down test significantly
            if get_sim_time(timeout_unit) > timeout:
                raise TimeoutError("Timed out waiting for test to end.")

            if all(
                [
                    monitor.in_flight == False
                    for monitor in self.output_monitors.values()
                ]
            ):
                break

        if self.fail_on_checks:
            for driver in self.input_drivers.values():
                assert driver.send_queue.empty(), "Driver still has data to send."


class CombinationalTestbench(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut)
        if not hasattr(self, "log"):
            self.log = SimLog("%s" % (type(self).__qualname__))

    def generate_inputs(self, num):
        '''
        We should generate dict of inputs and a list of related output for inputs
        For instance, the input disk should be
        self.inputs = {
                "data_in": [1,2,3,4],
                "shift_in": [1,2,3,4],
            },
        self.outputs = {
            "data_out": [1,2,3,4],
        }
        '''
        raise NotImplementedError

    def check_output(self, input, output):
        '''
        We should check the output is correct related to the input
        '''
        self.log.warning(f"check is bypassed")

    async def run_test(self, num):
        await Timer(5, units="ns")
        cocotb.log.info("Starting fp addition test")
        self.generate_inputs(num)
        for i in range (num):

            # load inputs
            for input_name, input_list in self.inputs.items():
                getattr(self.dut, input_name).value = input_list[i]

            await Timer(1, units="ns")

            # check outputs
            for output_name, output_list in self.outputs.items():
                expected_output = output_list[i]
                actual_output = getattr(self.dut, output_name).value
                self.output_name = output_name
                self.check_output(expected_output, actual_output)

        await Timer(num * 10, units="ns")

class StreamTestbench(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut)
        if not hasattr(self, "log"):
            self.log = SimLog("%s" % (type(self).__qualname__))


    def generate_inputs(self, num):
        '''
        We should generate dict of inputs and a list of related output for inputs
        For instance, the input disk should be
        self.inputs = {
                "data_in": [1,2,3,4],
                "shift_in": [1,2,3,4],
            },
        self.outputs = {
            "data_out": [1,2,3,4],
        }
        '''
        raise NotImplementedError

    def set_stream_driver(self, stream_driver):
        '''
        We should set the stream driver for the testbench
        For instance
        self.data_in_0_driver = StreamDriver(
            dut.clk,
            dut.data_in,
            dut.data_in_valid,
            dut.data_in_ready,
        )

        self.data_out_0_monitor = StreamMonitor(
            dut.clk,
            dut.data_out,
            dut.data_out_valid,
            dut.data_out_ready,
            check=False,
        )

        self.data_out_0_monitor.ready.value = 1

        self.data_in_0_driver.log.setLevel(logging.DEBUG)
        self.data_out_0_monitor.log.setLevel(logging.DEBUG)

        self.data_in_0_driver.load_driver(self.inputs["data_in_0"])
        self.data_out_0_monitor.load_monitor(self.outputs["data_out_0"])
        self.input_monitors = [self.data_in_0_driver]
        self.output_monitors = [self.data_out_0_monitor]
        '''
        raise NotImplementedError
    async def run_test(self, num, time_us):
        await self.reset()
        self.log.info("Reset finished")

        self.generate_inputs(num)
        self.set_stream_driver()
        await Timer(time_us, units="us")
        for monitor in self.output_monitors:
            assert monitor.exp_queue.empty(), "Monitor still has data to send."




