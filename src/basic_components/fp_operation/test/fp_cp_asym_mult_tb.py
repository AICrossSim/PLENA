#!/usr/bin/env python3

import logging
from re import A
import pytest
import cocotb
import sys
import os

from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

import torch

from cfl_cocotb import veri_runner
from cfl_cocotb.runner import SRC_PATH
from cfl_cocotb.testbench import CombinationalTestbench
from cfl_cocotb.fp_generation import TorchFpGenerator

from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware, pack_fp_to_bin
from cfl_tools.debugger import set_excepthook, get_dut_attributes


class FPCPAsymMultTB(CombinationalTestbench):
    def generate_inputs(self, num):
        # seed = torch.randint(0, 1000000, (1,)).item()
        torch.manual_seed(0)
        # self.log.info(f"seed : {seed}")
        q_config = {
            "exp_width_a" : self.dut.EXP_WIDTH_A.value,
            "mant_width_a" : self.dut.MANT_WIDTH_A.value,
            "exp_width_b" : self.dut.EXP_WIDTH_B.value,
            "mant_width_b" : self.dut.MANT_WIDTH_B.value,
            "ext_mant_width" : self.dut.EXT_MANT_WIDTH.value,
            "ext_exp_width" : self.dut.EXT_EXP_WIDTH.value,
        }

        exp_width = q_config["exp_width_a"]
        mant_width = q_config["mant_width_a"]
        ext_mant_width = q_config["ext_mant_width"]
        ext_exp_width = q_config["ext_exp_width"]

        torch_a = torch.randn(num) * 3 - 1.5
        torch_b = torch.randn(num) * 10 - 5

        width_a = q_config["mant_width_a"] + q_config["exp_width_a"]
        exponent_width_a = q_config["exp_width_a"]

        width_b = q_config["mant_width_b"] + q_config["exp_width_b"]
        exponent_width_b = q_config["exp_width_b"]

        qa, a_exp, a_mant = _minifloat_ieee_quantize_hardware(torch_a, width_a, exponent_width_a)
        qb, b_exp, b_mant = _minifloat_ieee_quantize_hardware(torch_b, width_b, exponent_width_b)

        out_width = q_config["mant_width_a"] + q_config["exp_width_a"] + q_config["ext_mant_width"] + q_config["ext_exp_width"] + 1
        out_exponent_width = q_config["exp_width_a"] + q_config["ext_exp_width"]

        out = qa * qb
        self.log.debug(f"out : {out}")
        debug_out, debug_exp, debug_mant = _minifloat_ieee_quantize_hardware(out, 6 + 8 + 1, 6)
        debug_out_bin = pack_fp_to_bin(debug_exp, debug_mant, 6, 8)
        self.log.debug(f"debug_out_bin : {debug_out_bin}")
        self.log.debug(f"debug_out : {debug_out}")
        self.log.debug(f"debug_exp : {debug_exp}")
        self.log.debug(f"debug_mant : {debug_mant}")
        _minifloat_ieee_quantize_hardware(torch.tensor([196]), 4,3)
        qout, out_exp, out_mant = _minifloat_ieee_quantize_hardware(out, out_width, out_exponent_width)

        inputs_a = pack_fp_to_bin(a_exp, a_mant, q_config["exp_width_a"], q_config["mant_width_a"])
        inputs_b = pack_fp_to_bin(b_exp, b_mant, q_config["exp_width_b"], q_config["mant_width_b"])

        outputs_out = pack_fp_to_bin(out_exp, out_mant, q_config["exp_width_a"] + q_config["ext_exp_width"], q_config["mant_width_a"] + q_config["ext_mant_width"])

        self.inputs = {
            "data_a": inputs_a.int().tolist(),
            "data_b": inputs_b.int().tolist(),
        }

        self.log.debug(f"input_0 : {qa}, {a_exp}, {a_mant}")
        self.log.debug(f"input_1 : {qb}, {b_exp}, {b_mant}")
        self.log.debug(f"output : {qout}, {out_exp}, {out_mant}")
        self.outputs = {
            "data_out": outputs_out.int().tolist(),
        }

    def check_output(self, input, output):
        self.log.debug(f"Expected result : {input}, got: {int(output)}")
        self.log.debug(f"----------------{self.dut}---------")
        get_dut_attributes(self.dut, self.log, None)
        if input != output:
            from lut_generation.generate_lut_fp import split_bin, fp_2_bin
            input_a = self.dut.data_a.value
            exp_a, mant_a = split_bin(input_a, self.dut.EXP_WIDTH_A.value, self.dut.MANT_WIDTH_A.value)
            data_a = mant_a * 2**exp_a
            print(f"data_a : {data_a}")

            input_b = self.dut.data_b.value
            exp_b, mant_b = split_bin(input_b, self.dut.EXP_WIDTH_B.value, self.dut.MANT_WIDTH_B.value)
            data_b = mant_b * 2**exp_b
            print(f"data_b : {data_b}")

            signed_mant_a = self.dut.signed_mant_a.value.signed_integer
            signed_mant_a_value = bin_2_int(signed_mant_a, self.dut.IN_FIXED_FRAC_WIDTH_A.value)
            print(f"signed_mant_a : {signed_mant_a_value}")
            signed_exp_a = self.dut.signed_exp_a.value
            signed_exp_a_value = bin_2_int(signed_exp_a, 0)
            print(f"signed_exp_a : {signed_exp_a_value}")
            mult_a = signed_mant_a_value * 2**signed_exp_a_value
            print(f"mult_a : {mult_a}")
            
            signed_mant_b = self.dut.signed_mant_b.value.signed_integer
            signed_mant_b_value = bin_2_int(signed_mant_b, self.dut.IN_FIXED_FRAC_WIDTH_B.value)
            print(f"signed_mant_b : {signed_mant_b_value}")
            signed_exp_b = self.dut.signed_exp_b.value
            signed_exp_b_value = bin_2_int(signed_exp_b, 0)
            print(f"signed_exp_b : {signed_exp_b_value}")
            mult_b = signed_mant_b_value * 2**signed_exp_b_value
            print(f"mult_b : {mult_b}")

            signed_mant_out = self.dut.signed_mant_out.value.signed_integer
            signed_mant_out_value = bin_2_int(signed_mant_out, self.dut.MULT_OUT_FIXED_FRAC_WIDTH.value)
            print(f"signed_mant_out : {signed_mant_out_value}")
            signed_exp_out = self.dut.signed_exp_out.value.signed_integer
            signed_exp_out_value = bin_2_int(signed_exp_out, 0)
            print(f"signed_exp_out : {signed_exp_out_value}")
            mult_out = signed_mant_out_value * 2**signed_exp_out_value
            print(f"mult_out : {mult_out}")
            # normalized_exp_out = self.dut.signed_exp_out.value
            # normalized_exp_out = bin_2_int(normalized_exp_out, self.dut.MULT_OUT_FIXED_FRAC_WIDTH.value)
            # print(f"normalized_exp_out : {normalized_exp_out}")

            print(f"input_a : {exp_a}, {mant_a}")
            print(f"input_b : {exp_b}, {mant_b}")
            print(f"normalized_data : {exp_out}, {mant_out}")
            breakpoint()
        # self.log.debug(f"----------------{self.dut.fp_casting}---------")
        # get_dut_attributes(self.dut.fp_casting, self.log, None)
        # self.log.debug(f"----------------{self.dut.fp_casting.fp_ieee_exponent_casting_inst}---------")
        # get_dut_attributes(self.dut.fp_casting.fp_ieee_exponent_casting_inst, self.log, None)
        # self.log.debug(f"----------------{self.dut.fp_casting.fp_ieee_mantissa_casting_inst}---------")
        # get_dut_attributes(self.dut.fp_casting.fp_ieee_mantissa_casting_inst, self.log, None)
        # self.log.debug(f"----------------{self.dut.fp_casting.fp_ieee_mantissa_casting_inst.round_to_nearest_even_inst}---------")
        # get_dut_attributes(self.dut.fp_casting.fp_ieee_mantissa_casting_inst.round_to_nearest_even_inst, self.log, None)

        assert input == output, f"Expected {input}, but got {int(output)}"

def bin_2_int(bin, FIXED_FRAC_WIDTH):
    return int(bin) * 2**(-FIXED_FRAC_WIDTH)

@cocotb.test()
async def test(dut):
    set_excepthook()
    tb = FPCPAsymMultTB(dut)
    tb.log.setLevel(logging.INFO)
    await tb.run_test(10)
    # try:
    #     tb = FPCPMultTB(dut)
    #     tb.log.setLevel(logging.DEBUG)
    #     await tb.run_test(10)
    # except Exception or AssertionError or AttributeError:
    #     set_excepthook()



@pytest.mark.dev
def test_fp_cp_asym_mult():
    # Run tests with different params
    veri_runner(
        group = "fp_operation",
        module = "fp_cp_asym_mult",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/buffer")
        ],
        module_param_list=[
            # {"EXP_WIDTH" : 4, "MANT_WIDTH" : 3, "EXT_MANT_WIDTH" : 0, "EXT_EXP_WIDTH" : 0},
            {
                "EXP_WIDTH_A" : 4, 
                "MANT_WIDTH_A" : 3, 
                "EXP_WIDTH_B" : 4, 
                "MANT_WIDTH_B" : 3, 
                "EXT_MANT_WIDTH" : 3, 
                "EXT_EXP_WIDTH" : 1,
            },
            # {"EXP_WIDTH" : 1, "MANT_WIDTH" : 6, "EXT_MANT_WIDTH" : 0, "EXT_EXP_WIDTH" : 0},
        ],
        trace = False,
    )

if __name__ == "__main__":
    test_fp_cp_asym_mult()