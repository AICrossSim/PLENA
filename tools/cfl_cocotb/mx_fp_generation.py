import math
from typing import List, Tuple
from cfl_cocotb import FpGenerator
import random

def split_bitstream_equal(bitstream_val, chunk_width):

    if hasattr(bitstream_val, 'integer'):
        val = bitstream_val.integer
    else:
        val = int(bitstream_val)

    total_bits = bitstream_val.n_bits if hasattr(bitstream_val, 'n_bits') else val.bit_length()
    # Pad to multiple of chunk_width if needed
    total_bits = ((total_bits + chunk_width - 1) // chunk_width) * chunk_width

    chunks = []
    for i in reversed(range(0, total_bits, chunk_width)):
        chunk = (val >> i) & ((1 << chunk_width) - 1)
        chunks.append(chunk)
    return chunks


class MXBlockFPConverter:
    def __init__(self, elem_exp_width: int, elem_mant_width: int, scale_width: int, block_size: int):
        self.elem_exp_width = elem_exp_width
        self.elem_mant_width = elem_mant_width
        self.scale_width = scale_width
        self.scale_bias = (1 << (scale_width - 1)) - 1
        self.block_size = block_size
        self.element_gen = FpGenerator(elem_exp_width, elem_mant_width)

    def _get_shared_exponent(self, values: List[float]) -> int:
        max_val = max(abs(v) for v in values if v != 0)
        if max_val == 0:
            return 0 
        exponent = int(math.floor(math.log2(max_val)))
        biased_exp = exponent + self.scale_bias
        if biased_exp >= (1 << self.scale_width):
            raise OverflowError("Exponent overflow for MX-FP format.")
        elif biased_exp <= 0:
            raise ValueError("Underflow: subnormals not supported.")
        return biased_exp

    def convert_block(self, values: List[float]) -> Tuple[int, List[Tuple[int, int]]]:
        shared_exp = self._get_shared_exponent(values)
        raw_exp = shared_exp - self.scale_bias
        encoded_vals = []
        for val in values:
            divided_val = val / (2 ** raw_exp) if val != 0 else 0
            encoded_vals.append(self.element_gen.float_to_custom_fp(divided_val))
        return shared_exp, encoded_vals
    
    def generate_block(self, amount, lower_bound=-1.0, upper_bound=1.0) -> List[float]:
        fp_values = []
        for _ in range(amount):
            val = random.uniform(lower_bound, upper_bound)
            fp_values.append(val)
        return fp_values
    
    def generate_certain_values(self, values: List[float]) -> List[float]:
        mxfp_scales = []
        mxfp_elems = []
        for i in range(len(values) // self.block_size):
            mxfp_scale, mxfp_elem = self.convert_block(values[i * self.block_size:(i + 1) * self.block_size])
            mxfp_scales.append(mxfp_scale)
            mxfp_elems.append(mxfp_elem)
        return mxfp_scales, mxfp_elems

    
    def convert_to_float(self, elements, scale, element_exp_width=4, element_mant_width=3):
        scale = 2 ** (scale - self.scale_bias)
        result_fp = []
        for element in elements:
            print(f"Element: {element}, Scale: {scale}")
            # print(self.element_gen.full_precision_fp_float_convertion(element_ext_exp_width, element_ext_mant_width, element))
            result_fp.append(scale * self.element_gen.full_precision_fp_float_convertion(element_exp_width, element_mant_width, element))
        return result_fp
    
    def blockwise_convert_to_float(self, elements, scales, block_num, element_exp_width=4, element_mant_width=3):
        scale_array     = split_bitstream_equal(scales, self.scale_width)
        elements_array  = split_bitstream_equal(elements, (element_exp_width + element_mant_width + 1) * self.block_size)
        result_fp = []
        for i in range(block_num):
            result_fp.append(self.convert_block_to_fp(elements_array[i], scale_array[i], element_exp_width, element_mant_width))
        return result_fp
    
    def convert_block_to_fp(self, elements, scale, element_exp_width=4, element_mant_width=3):
        true_scale = 2 ** (scale - self.scale_bias)
        extracted_elements = split_bitstream_equal(elements, (element_exp_width + element_mant_width + 1) )
        result_fp = []
        for element in extracted_elements:
            result_fp.append(true_scale * self.element_gen.full_precision_fp_float_convertion(self.elem_exp_width, self.elem_mant_width, element))
        return result_fp

if __name__ == "__main__":
    converter = MXBlockFPConverter(elem_exp_width=4, elem_mant_width=3, scale_width=8, block_size=4)
    float_array = [3.14, -2.7, 4.0, 1.0]
    shared_exp, encoded_vals = converter.convert_block(float_array)
    print("Shared exponent (biased):", shared_exp)
    print("Encoded values (sign, mantissa):", encoded_vals)
    decoded_vals = converter.convert_to_float(encoded_vals, shared_exp)
    print("Decoded values:", decoded_vals)

