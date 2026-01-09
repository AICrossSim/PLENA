#!/usr/bin/env python3

import logging
import pytest
import cocotb
import torch

from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
from cocotb.log import SimLog

from cfl_cocotb import veri_runner
from cfl_cocotb.runner import SRC_PATH
from cfl_cocotb.testbench import Testbench
from cfl_cocotb.streaming import StreamDriver
from cfl_cocotb.torch_fp_conversion import pack_fp_to_bin

from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware


class TopkTB(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut, dut.clk, dut.rst)

        if not hasattr(self, "log"):
            self.log = SimLog("%s" % (type(self).__qualname__))
            self.log.setLevel(logging.DEBUG)

        # Input driver: single data stream
        self.in_driver = StreamDriver(
            dut.clk, dut.in_data, dut.data_in_valid, dut.data_in_ready
        )

    def generate_inputs(self, num_data):
        """
        Generate a sequence of floating point inputs and compute the expected top-K.
        """
        exp_width = self.dut.EXP_WIDTH.value
        mant_width = self.dut.MANT_WIDTH.value
        k = self.dut.K.value
        data_width = exp_width + mant_width + 1

        torch.manual_seed(42)
        # Generate random floats
        torch_data = torch.randn(num_data) * 10

        # Quantize to hardware format
        q_data, data_exp, data_mant = _minifloat_ieee_quantize_hardware(
            torch_data, data_width, exp_width
        )

        # Pack each input into binary format
        packed_inputs = pack_fp_to_bin(data_exp, data_mant, exp_width, mant_width)
        self.inputs = [int(packed_inputs[i]) for i in range(num_data)]

        # Compute expected top-K using torch
        # Sort in descending order and take top K values
        sorted_vals, sorted_indices = torch.sort(q_data, descending=True)
        topk_vals = sorted_vals[:k]
        topk_indices = sorted_indices[:k]

        # Pack expected top-K values into binary format
        topk_q, topk_exp, topk_mant = _minifloat_ieee_quantize_hardware(
            topk_vals, data_width, exp_width
        )
        self.expected_topk_packed = pack_fp_to_bin(topk_exp, topk_mant, exp_width, mant_width)
        self.expected_topk_vals = topk_vals
        self.expected_indices = topk_indices

        self.log.info(f"Input data (quantized): {q_data.tolist()}")
        self.log.info(f"Expected top-{k} values: {topk_vals.tolist()}")
        self.log.info(f"Expected top-{k} indices: {topk_indices.tolist()}")

    async def run_test(self, us, num_data):
        await self.reset()
        self.log.info("Reset finished")
        self.dut.data_out_ready.value = 1

        self.generate_inputs(num_data)

        # Load all inputs into the driver
        self.in_driver.load_driver(self.inputs)

        await Timer(100, units="ns")

        # Wait for all inputs to be consumed
        while not self.in_driver.send_queue.empty():
            await RisingEdge(self.dut.clk)

        # Wait a few more cycles for the output to settle
        for _ in range(10):
            await RisingEdge(self.dut.clk)

        # Now manually check the final top-K output
        k = self.dut.K.value
        data_width = self.dut.EXP_WIDTH.value + self.dut.MANT_WIDTH.value + 1

        # Read the packed topk_val output
        topk_val_packed = int(self.dut.topk_val.value)
        topk_idx_packed = int(self.dut.topk_idx.value)

        self.log.info(f"DUT topk_val (packed): {topk_val_packed:#x}")
        self.log.info(f"DUT topk_idx (packed): {topk_idx_packed:#x}")

        # Unpack and compare each slot
        errors = []
        for i in range(k):
            # Extract individual values from packed output
            mask = (1 << data_width) - 1
            got_val = (topk_val_packed >> (i * data_width)) & mask
            expected_val = int(self.expected_topk_packed[i])

            self.log.info(f"Slot {i}: Got val={got_val:#x}, Expected val={expected_val:#x}")

            if got_val != expected_val:
                errors.append(f"Slot {i}: Got {got_val:#x}, Expected {expected_val:#x}")

        if errors:
            for e in errors:
                self.log.error(e)
            assert False, f"Top-K value mismatch: {errors}"

        self.log.info("Test PASSED: Top-K values match!")


@cocotb.test()
async def test(dut):
    tb = TopkTB(dut)
    tb.log.setLevel(logging.DEBUG)
    # NUM_DATA should match the parameter in the DUT
    num_data = dut.NUM_DATA.value
    await tb.run_test(us=50, num_data=num_data)


@pytest.mark.dev
def test_topk():
    veri_runner(
        group="common",
        module="topk",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/fp_operation"),
            str(SRC_PATH / "basic_components/buffer"),
        ],
        module_param_list=[
            {"EXP_WIDTH": 5, "MANT_WIDTH": 10, "NUM_DATA": 16, "K": 4},
            {"EXP_WIDTH": 4, "MANT_WIDTH": 3, "NUM_DATA": 8, "K": 2},
        ],
        trace=True,
    )


if __name__ == "__main__":
    test_topk()
