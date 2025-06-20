from math import e, exp
from re import L
import sys
from sympy.external.gmpy import bit_scan0
import torch
import pdb
import torch.nn as nn
import torch.nn.functional as F
import pdb
from bitstring import BitArray
from functools import partial
from pathlib import Path
from lut_generation.generate_lut_base import FUNCTION_TABLE, GenerateSVLut
from bitstring import BitArray
from quant.quantizer.hardware_quantizer.utils import pack_fp_to_bin
from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware

class GenerateSVLutFP(GenerateSVLut):
    def __init__(
        self, 
        function_name, 
        save : bool = False, 
        exp_width: int = 4, 
        mant_width: int = 3,
        out_exp_width: int = 4, 
        out_mant_width: int = 3):
        super().__init__(function_name, save)
        self.exp_width = exp_width
        self.mant_width = mant_width
        self.out_exp_width = out_exp_width
        self.out_mant_width = out_mant_width

    def generate_lut(self):
        entry_list = range(0, 2**(1+self.exp_width + self.mant_width))
        lut = {}
        for i in entry_list:
            exp, mant = split_bin(i, self.exp_width, self.mant_width)
            fp = 2**exp * mant
            target_fp =self.f(torch.tensor(fp))
            target_bin = fp_2_bin(target_fp, self.out_exp_width, self.out_mant_width)
            in_bin = BitArray(uint=i, length=self.exp_width + self.mant_width + 1).bin
            out_bin = BitArray(uint=target_bin, length=self.out_exp_width + self.out_mant_width + 1).bin
            lut[in_bin] = out_bin

        self.lut_dict = {
            "in_entry_width": self.exp_width + self.mant_width + 1,
            "out_entry_width": self.out_exp_width + self.out_mant_width + 1,
            "quant_info": f"quant_type: e{self.exp_width}m{self.mant_width} to e{self.out_exp_width}m{self.out_mant_width}",
            "lut": lut,
        }

def split_bin(bits: int, exp_width: int, mant_width: int):
    bin = BitArray(uint=bits, length=exp_width + mant_width + 1)
    sign = bin[0]
    exponent_bits = bin[1:exp_width + 1]
    mantissa_bits = bin[exp_width + 1:]

    exponent = int(exponent_bits.bin, 2)
    mantissa = int(mantissa_bits.bin, 2)
    # Bias and reconstruct
    bias = (1 << (exp_width - 1)) - 1
    exponent_val = exponent - bias
    exponent_min = 0 - bias

    if exponent_val == exponent_min:
        mantissa_val = mantissa / (1 << mant_width)
    else:
        mantissa_val = 1.0 + (mantissa / (1 << mant_width))

    return exponent_val, - mantissa_val if sign else mantissa_val

def fp_2_bin(fp, exp_width, mant_width):
    fp = torch.tensor(fp)
    fp, exp, mant = _minifloat_ieee_quantize_hardware(fp, exp_width + mant_width + 1, exp_width)
    bin = pack_fp_to_bin(exp, mant, exp_width, mant_width)
    return bin

def test_fp_bin_conversion():
    exp_width = 4
    mant_width = 3
    for i in range(0, 2**(exp_width + mant_width)):
        exp, mant = split_bin(i, exp_width, mant_width)
        if exp == 2**(exp_width - 1):
            # cannot handle infinity
            continue
        if i == 2**(exp_width + mant_width):
            # cannot handle -0.0
            continue
        fp = torch.tensor(mant * 2**exp)
        fp_bin = fp_2_bin(fp, exp_width, mant_width)
        assert i == fp_bin, f"i: {i} != fp_bin: {fp_bin}"
    
def test_lut_generation_pipeline():
    from cfl_tools.logger import get_logger, set_logging_verbosity
    set_logging_verbosity("debug")
    logger = get_logger(__name__)
    logger.info("Starting test_lut_generation_pipeline")
    gen_lut = GenerateSVLutFP(
        function_name="exp", 
        save=True,
        exp_width=1, 
        mant_width=1, 
        out_exp_width=1, 
        out_mant_width=1,
    )
    gen_lut.generate_lut()
    sv_file = gen_lut.generate_sv()
    print(sv_file)
    gen_lut.pipeline()


if __name__ == "__main__":
    # test_fp_bin_conversion()
    test_lut_generation_pipeline()

