from dataclasses import dataclass
import re

@dataclass
class MXFPMeta:
    block_size: int
    scale_exp_bits: int
    element_exp_bits: int
    element_frac_bits: int

    @classmethod
    def from_string(cls, name: str) -> "MXFPMeta":
        # Strict format: MXFP_E<exp>M<frac>_B<block>_S<scale>, e.g:MXFP_E4M3_B32_S8
        match = re.fullmatch(r"MXFP_E(\d+)M(\d+)_B(\d+)_S(\d+)", name)
        if not match:
            raise ValueError(f"Invalid MXFPMeta string: {name} (expected format: MXFP_E<exp>M<frac>_B<block>_S<scale>)")

        element_exp_bits = int(match.group(1))
        element_frac_bits = int(match.group(2))
        block_size = int(match.group(3))
        scale_exp_bits = int(match.group(4))

        return cls(
            block_size=block_size,
            scale_exp_bits=scale_exp_bits,
            element_exp_bits=element_exp_bits,
            element_frac_bits=element_frac_bits,
        )
 
@dataclass
class MXFPTensorMeta:
    device: str
    dtype: str
    shape: tuple[int, ...]
    block_dim: int
    meta: MXFPMeta