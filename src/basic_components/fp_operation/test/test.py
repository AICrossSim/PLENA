#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os

# from cocotb.triggers import Timer, RisingEdge
# from cocotb.clock import Clock

# from cfl_cocotb import veri_runner
# from cfl_cocotb.runner import SRC_PATH
# from cfl_cocotb.testbench import CombinationalTestbench
# from cfl_cocotb.fp_generation import TorchFpGenerator

import math

def clamp(exponent, mantissa, exp_width, mant_width):
    exp_max = 2**(exp_width) - 2 # -2 due to the special case of inf
    exp_min = -2**(exp_width)
    new_exp = max(min(exponent, exp_max), exp_min)

    sign = 1 if mantissa >= 0 else -1

    if (new_exp == exp_min):
        mant_max = 2**(mant_width) - 1
        mant_min = 0
    else:
        mant_max = 2**(mant_width + 1) - 1
        mant_min = 0

    mantissa = (mantissa * 2**(mant_width + exponent - new_exp))
    mantissa = round(mantissa)
    mantissa = max(min(mantissa, mant_max), mant_min)
    mantissa = mantissa / 2**(mant_width)

    return new_exp, mantissa

def parse_fp_input(x, config):
    exp_width = config["EXP_WIDTH"]
    mant_width = config["MANT_WIDTH"]

    mantissa, exponent = math.frexp(x)

    mantissa *= 2
    exponent -= 1

    exp, mant = clamp(exponent, mantissa, exp_width, mant_width)
    return exp, mant

def fp_add_hardware(a, b, config):
    a_exp, a_mant = parse_fp_input(a, config["a_config"])
    b_exp, b_mant = parse_fp_input(b, config["b_config"])
    print(f"\na: {a}")
    logging_fp(a_exp, a_mant)
    print(f"\nb: {b}")
    logging_fp(b_exp, b_mant)

    out_mant_width = config["OUT_MANT_WIDTH"]
    out_exp_width = config["OUT_EXP_WIDTH"]

    if a_exp == b_exp:
        mant_sum = a_mant + b_mant
        exp_sum = a_exp
    elif a_exp > b_exp:
        b_mant = b_mant * 2**config["b_config"]["MANT_WIDTH"] / 2**(a_exp - b_exp)
        mant_sum = a_mant + b_mant
        exp_sum = a_exp
    else:
        a_mant = a_mant / 2**(b_exp - a_exp)
        mant_sum = b_mant + a_mant
        exp_sum = b_exp

    breakpoint()
    exp, mant = clamp(exp_sum, mant_sum, out_exp_width, out_mant_width)
    return exp, mant

def logging_fp(exp, mant):
    print(f"value: {mant * 2**(exp)}, exp: {exp}, mant: {mant}")

import random
if __name__ == "__main__":
    a = random.random()
    b = random.random()
    config = {
        "a_config": {"EXP_WIDTH": 4, "MANT_WIDTH": 4},
        "b_config": {"EXP_WIDTH": 4, "MANT_WIDTH": 4},
        "OUT_MANT_WIDTH": 4,
        "OUT_EXP_WIDTH": 4,
    }
    exp, mant = fp_add_hardware(a, b, config)
    print("output")
    logging_fp(exp, mant)
    print(a + b)