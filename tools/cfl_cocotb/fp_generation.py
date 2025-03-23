import random
import math

def get_fp_range(exp_width, mant_width):
    bias = (1 << (exp_width - 1)) - 1
    max_exponent = (1 << exp_width) - 2  # reserve top exp for inf/Nan if applicable
    min_exponent = 1  # 0 usually for subnormals

    max_val = (2 - 2**(-mant_width)) * (2 ** (max_exponent - bias))
    min_val = 1.0 * (2 ** (min_exponent - bias))
    return min_val, max_val

class FpGenerator:
    def __init__(self, exp_width, mant_width):
        self.exp_width = exp_width
        self.mant_width = mant_width
        self.min_val, self.max_val = get_fp_range(exp_width, mant_width)

    def generate_fp_input(self, amount):
        fp_values = []
        results = []
        for _ in range(amount):
            val = random.uniform(self.min_val, self.max_val)
            fp_values.append(val)
            fp_bits = self.float_to_custom_fp(val)
            results.append(fp_bits)
            print(f"Value: {val}, Binary: {bin(fp_bits)}")
        return fp_values, results
    
    def generate_boundary_values(self):
        negative_max = self.float_to_custom_fp(-self.max_val)
        negative_min = self.float_to_custom_fp(-self.min_val)
        positive_max = self.float_to_custom_fp(self.max_val)
        positive_min = self.float_to_custom_fp(self.min_val)
        return negative_max, negative_min, positive_max, positive_min

    def float_to_custom_fp(self, val):
        """Convert Python float to custom binary FP format: {sign, exp, mant}"""
        if val == 0.0:
            return 0

        # Get sign
        sign = 0 if val >= 0 else 1
        val = abs(val)

        # Get raw exponent and mantissa
        exponent = int(math.floor(math.log2(val)))
        mantissa_val = val / (2 ** exponent) - 1.0  # remove leading 1

        # Bias the exponent
        bias = (1 << (self.exp_width - 1)) - 1
        exponent_bits = exponent + bias
        if exponent_bits < 0 or exponent_bits >= (1 << self.exp_width):
            raise ValueError("Exponent out of range!")

        # Mantissa
        mantissa_bits = int(mantissa_val * (1 << self.mant_width))

        # Pack into integer: {sign, exp, mant}
        result = (sign << (self.exp_width + self.mant_width)) | (exponent_bits << self.mant_width) | mantissa_bits
        return result

    def custom_fp_to_float(self, bits):
        """Convert from custom FP format to Python float"""
        total_width = 1 + self.exp_width + self.mant_width
        sign = (bits >> (self.exp_width + self.mant_width)) & 0x1
        exponent_bits = (bits >> self.mant_width) & ((1 << self.exp_width) - 1)
        mantissa_bits = bits & ((1 << self.mant_width) - 1)

        # Bias and reconstruct
        bias = (1 << (self.exp_width - 1)) - 1
        exponent = exponent_bits - bias
        mantissa_val = 1.0 + (mantissa_bits / (1 << self.mant_width))

        val = mantissa_val * (2 ** exponent)
        return -val if sign == 1 else val
    

    def full_precision_fp_float_convertion(self, output_exp_width, output_man_width, bits):
        total_width = 1 + output_exp_width + output_man_width
        sign = (bits >> (output_exp_width + output_man_width)) & 0x1
        exponent_bits = (bits >> output_man_width) & ((1 << output_exp_width) - 1)
        mantissa_bits = bits & ((1 << output_man_width) - 1)

        # Bias and reconstruct
        bias = (1 << (output_exp_width - 1)) - 1
        exponent = exponent_bits - bias
        mantissa_val = 1.0 + (mantissa_bits / (1 << output_man_width))

        val = mantissa_val * (2 ** exponent)
        return -val if sign == 1 else val





if __name__ == "__main__":
    exp_width = 4
    mant_width = 3
    generator = FpGenerator(exp_width, mant_width)
    generator.generate_fp_input(10)