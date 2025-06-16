#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os

from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

from cfl_cocotb import veri_runner
from cfl_cocotb.runner import SRC_PATH
from cfl_cocotb.testbench import CombinationalTestbench
from cfl_cocotb.fp_generation import TorchFpGenerator

class FPAddTB(CombinationalTestbench):
    def generate_inputs(self, num):
        exp_width = self.dut.EXP_WIDTH.value
        mant_width = self.dut.MANT_WIDTH.value
        ext_mant_width = self.dut.EXT_MANT_WIDTH.value
        ext_exp_width = self.dut.EXT_EXP_WIDTH.value

        input_generator = TorchFpGenerator(exp_width, mant_width)
        input_generator.max_val = 2.0
        input_generator.min_val = -2.0
        output_generator = TorchFpGenerator(exp_width + ext_exp_width, mant_width + ext_mant_width)


        fp_outputs = []
        outputs_out = []
        fp_data_in_0, data_in_0 = input_generator.generate_fp_input(num)
        fp_data_in_1, data_in_1 = input_generator.generate_fp_input(num)
        inputs_a = data_in_0
        inputs_b = data_in_1

        for i in range(num):
            fp_outputs.append(fp_data_in_0[i] + fp_data_in_1[i])
            outputs_out.append(output_generator.fp2bin(fp_outputs[i]))

        self.inputs = {
            "data_a": inputs_a,
            "data_b": inputs_b,
        }

        self.log.debug(f"input_0 : {fp_data_in_0}, Converted bin : {data_in_0}")
        self.log.debug(f"input_1 : {fp_data_in_1}, Converted bin : {data_in_1}")
        self.log.debug(f"output : {fp_outputs}, Converted output : {outputs_out}")
        self.outputs = {
            "data_out": outputs_out,
        }

    def check_output(self, input, output):
        self.log.debug(f"Expected result : {input}, got: {int(output)}")

        assert input == output, f"Expected {input}, but got {int(output)}"

@cocotb.test()
async def test(dut):
    tb = FPAddTB(dut)
    tb.log.setLevel(logging.DEBUG)
    await tb.run_test(10)
    # try:
    #     tb = FPExpTB(dut)
    #     await tb.run_test(10)
    # except Exception as e:
    #     print("\nEntering debugger...")
    #     pdb.post_mortem(sys.exc_info()[2])
# @cocotb.test()



@pytest.mark.dev
def test_simple_fp_addition():
    # Run tests with different params
    veri_runner(
        group = "fp_operation",
        module = "fp_cp_adder_v1",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/buffer")
        ],
        module_param_list=[
            {"EXP_WIDTH" : 4, "MANT_WIDTH" : 3, "EXT_MANT_WIDTH" : 0, "EXT_EXP_WIDTH" : 0},
            # {"EXP_WIDTH" : 3, "MANT_WIDTH" : 4, "EXT_MANT_WIDTH" : 0, "EXT_EXP_WIDTH" : 0},
            # {"EXP_WIDTH" : 1, "MANT_WIDTH" : 6, "EXT_MANT_WIDTH" : 0, "EXT_EXP_WIDTH" : 0},
        ],
        trace = False,
    )

if __name__ == "__main__":
    test_simple_fp_addition()