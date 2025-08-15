from dataclasses import dataclass
import re

@dataclass
class MinifloatMeta:
    element_exp_bits: int
    element_frac_bits: int
    element_is_finite: bool

    @classmethod
    def from_string(cls, name: str) -> "MinifloatMeta":
        # Strict format: MINIFLOAT_E<exp>M<frac>, e.g:MINIFLOAT_E4M3
        match = re.fullmatch(r"MINIFLOAT_E(\d+)M(\d+)", name)
        if not match:
            raise ValueError(f"Invalid MinifloatMeta string: {name} (expected format: MINIFLOAT_E<exp>M<frac>)")

        element_exp_bits = int(match.group(1))
        element_frac_bits = int(match.group(2))
        element_is_finite = True

        return cls(
            element_exp_bits=element_exp_bits,
            element_frac_bits=element_frac_bits,
            element_is_finite=element_is_finite,
        )
 
@dataclass
class MinifloatTensorMeta:
    device: str
    dtype: str
    shape: tuple[int, ...]
    meta: MinifloatMeta