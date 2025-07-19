#!/usr/bin/env python3

import logging, pdb, sys, traceback
import torch, math
from pathlib import Path

import cocotb
from cocotb.log import SimLog
from cocotb.triggers import *

from cfl_cocotb.testbench import Testbench, CombinationalTestbench
from cfl_cocotb.streaming import (
    StreamDriver,
    StreamMonitor,
)
from cfl_cocotb.runner import veri_runner, SRC_PATH
from cfl_cocotb.torch_fp_conversion import fp_2_bin, bin_2_fp
from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware
from cfl_tools.debugger import set_excepthook, get_dut_attributes

logger = logging.getLogger("testbench")
logger.setLevel(logging.DEBUG)

src_path = Path(__file__).parent.parent.parent

torch.manual_seed(10)


class MXFP2FPUnary(CombinationalTestbench):
    def generate_inputs(self, num):
        self.q_config = {
            "mxfp_exp_width": self.dut.MXFP_EXP_WIDTH.value,
            "mxfp_mant_width": self.dut.MXFP_MANT_WIDTH.value,
            "mxfp_scale_width": self.dut.MXFP_SCALE_WIDTH.value,
            "fp_exp_width": self.dut.FP_EXP_WIDTH.value,
            "fp_mant_width": self.dut.FP_MANT_WIDTH.value,
        }
        
        # Generate random inputs between -1 and 1
        torch.manual_seed(10)
        x = torch.rand(1, num) * 10 - 5
        from quant.quantizer.hardware_quantizer import _mx_fp_quantize_hardware
        from cfl_cocotb.torch_fp_conversion import pack_fp_to_bin, fp_2_bin
        bm_x, per_block_fp_exp, per_block_fp_mant, scale = _mx_fp_quantize_hardware(
            x, 
            self.q_config["mxfp_exp_width"] + self.q_config["mxfp_mant_width"] + 1, 
            self.q_config["mxfp_exp_width"], 
            self.q_config["mxfp_scale_width"], 
            [1,1]
        )

        fp_inputs = pack_fp_to_bin(
            per_block_fp_exp, per_block_fp_mant, 
            self.q_config["mxfp_exp_width"], 
            self.q_config["mxfp_mant_width"]
        )

        self.log.debug(f"Input Packed FP: {fp_inputs}")
        q_fp, fp_outs = fp_2_bin(
            bm_x, 
            self.q_config["fp_exp_width"], 
            self.q_config["fp_mant_width"]
        )
        self.log.debug(f"quant input: {bm_x}")
        self.log.debug(f"quant q_fp: {q_fp}")

        self.inputs = {
            "element_data_in": fp_inputs.reshape(-1).int().tolist(),
            "scale_data_in": scale.reshape(-1).int().tolist(),
        }

        self.outputs = {
            "fp_out": fp_outs.reshape(-1).int().tolist(),
        }
        
    def check_output(self, input, output):
        from cfl_cocotb.torch_fp_conversion import bin_2_fp
        expected_result = bin_2_fp(self.dut.normalized_data.value.integer, self.dut.NORMALIZE_OUT_EXP_WIDTH.value, self.dut.NORMALIZE_OUT_MANT_WIDTH.value)
        self.log.debug(f"Expected result : {expected_result}")
        self.log.debug(f"Expected result : {input}, got: {int(output.integer)}")
        self.log.debug(f"----------------{self.dut}---------")
        # get_dut_attributes(self.dut, self.log, None)
        # self.log.debug(f"----------------{self.dut.fp_ieee_exponent_casting_inst}---------")
        # get_dut_attributes(self.dut.fp_ieee_exponent_casting_inst, self.log, None)
        # self.log.debug(f"----------------{self.dut.fp_ieee_mantissa_casting_inst}---------")
        # get_dut_attributes(self.dut.fp_ieee_mantissa_casting_inst, self.log, None)

        assert input == int(output.integer), f"Expected {input}, but got {int(output.integer)}"

@cocotb.test()
async def test(dut):
    tb = MXFP2FPUnary(dut)
    tb.log.setLevel(logging.DEBUG)
    await tb.run_test(10)

if __name__ == "__main__":
    veri_runner(
        trace=True, 
        module="mx_fp_2_fp_unary",
        group="vector_machine",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/buffer"),
            str(SRC_PATH / "basic_components/fp_operation"),
            str(SRC_PATH / "basic_components/int_operation"),
            str(SRC_PATH / "basic_components/conversion")
        ],
        module_param_list=[
            {
                "MXFP_EXP_WIDTH": 4,
                "MXFP_MANT_WIDTH": 3,
                "MXFP_SCALE_WIDTH": 8,
                "FP_EXP_WIDTH": 8,
                "FP_MANT_WIDTH": 7
            }
        ]
    )
