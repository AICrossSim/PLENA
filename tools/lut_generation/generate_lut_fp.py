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

class GenerateSVLutFP(GenerateSVLut):
    def __init__(self, function_name, parameter, path):
        super().__init__(function_name, parameter, path)

    def quant_profile(self, bin_in):
        return bin_in

    def generate_lut_address(self, lut_address: list):
        return NotImplementedError

    def generate_lut(self, lut_address: list):
        return NotImplementedError
    
    def generate_sv(self,lut):
        return NotImplementedError

def bin_to_fp(bin_in, exp_width, mant_width):
    exp_bin, mant_bin = bin_in[:exp_width], bin_in[exp_width:]
    exp = int(exp_bin, 2)
    mant = int(mant_bin, 2)
    return exp, mant

def fp_to_bin(exp, mant, exp_width, mant_width):
    exp_bin = bin(exp)[2:].zfill(exp_width)
    mant_bin = bin(mant)[2:].zfill(mant_width)
    return exp_bin + mant_bin

def doubletofx(data_width: int, f_width: int, num: float, type="hex"):
    assert type == "bin" or type == "hex", "type can only be: 'hex' or 'bin'"
    intnum = int(num * 2 ** (f_width))
    intbits = BitArray(int=intnum, length=data_width)
    return str(intbits.bin) if type == "bin" else str(intbits)

def bin2fp(bits: int, exp_width: int, mant_width: int):
    """Convert from bits to Python float"""
    bin = BitArray(int=bits, length=exp_width + mant_width + 1)
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

    val = mantissa_val * (2 ** exponent_val)
    return -val if sign == 1 else val

from bitstring import BitArray
def fp_2_bin(fp, exp_width, mant_width):
    fp = torch.tensor(fp)
    from quant.quantizer.hardware_quantizer.utils import pack_fp_to_bin
    from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware
    fp, exp, mant = _minifloat_ieee_quantize_hardware(fp, exp_width + mant_width + 1, exp_width)
    bin = pack_fp_to_bin(exp, mant, exp_width, mant_width)
    return bin
if __name__ == "__main__":
    exp_width = 4
    mant_width = 3
    print(bin2fp(3*16 + 13, 4, 3))
    breakpoint()
    for i in range(255):
        fp = bin2fp(i, 4, 3)
        fp = torch.tensor(fp)
        fp_bin = fp_2_bin(fp, 4, 3)
        print(i, fp_bin)
        assert i == fp_bin, f"i: {i} != fp_bin: {fp_bin}"

