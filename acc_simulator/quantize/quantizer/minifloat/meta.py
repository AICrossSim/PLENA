from dataclasses import dataclass
import re

@dataclass
class MinifloatMeta:
    element_exp_bits: int                 
    element_frac_bits: int
    exponent_bias: int | None = None

    def __post_init__(self):
        # Set default bias (IEEE style)
        if self.exponent_bias is None:
            self.exponent_bias = (2 ** (self.element_exp_bits - 1)) - 1

        assert self.exponent_bias >= 0, "Exponent bias must be non-negative."

    @classmethod
    def from_string(cls, name: str) -> "MinifloatMeta":
        """
        Parse strings like:
        - FP_E4M3          (auto bias)
        - FP_E4M3_B7    (explicit bias)
        """
        match = re.fullmatch(r"FP_E(\d+)M(\d+)(?:_B(\d+))?", name)
        if not match:
            raise ValueError(
                f"Invalid MinifloatMeta string: '{name}'. "
                f"Expected format: FP_E<exp>M<frac>[_B<bias>]"
            )

        exp_bits = int(match.group(1))
        frac_bits = int(match.group(2))
        bias = int(match.group(3)) if match.group(3) else None

        return cls(
            element_exp_bits=exp_bits,
            element_frac_bits=frac_bits,
            exponent_bias=bias,
        )