from dataclasses import dataclass

@dataclass
class MinifloatMeta:
    element_exp_bits: int                 
    element_frac_bits: int
    exponent_bias: int | None = None

    def __post_init__(self):
        self.element_bits = self.element_exp_bits + self.element_frac_bits + 1

        legal_exp_frac = ((5, 2), (4, 3), (3, 4), (3, 2), (2, 3), (2, 1))
        # if (self.element_exp_bits, self.element_frac_bits) not in legal_exp_frac:
        #     print(f"[Warning] ({self.element_exp_bits}, {self.element_frac_bits}) not in known configs")

        # Set default bias (IEEE style)
        if self.exponent_bias is None:
            self.exponent_bias = (2 ** (self.element_exp_bits - 1)) - 1

        assert self.exponent_bias >= 0, "Exponent bias must be non-negative."

FP8_E4M3 = MinifloatMeta(
    element_exp_bits=4,
    element_frac_bits=3,
    exponent_bias=None,
)

FP8_E5M2 = MinifloatMeta(
    element_exp_bits=5,
    element_frac_bits=2,
    exponent_bias=None,
)

FP16_E8M7 = MinifloatMeta(
    element_exp_bits=8,
    element_frac_bits=7,
    exponent_bias=None,
)

FP16_E5M10 = MinifloatMeta(
    element_exp_bits=5,
    element_frac_bits=10,
    exponent_bias=None,
)

FP10_E6M3= MinifloatMeta(
    element_exp_bits=6,
    element_frac_bits=3,
    exponent_bias=None,
)