from dataclasses import dataclass
import re

@dataclass
class MXIntMeta:
    block_size: int
    scale_bits: int
    element_bits: int

    @classmethod
    def from_string(cls, name: str) -> "MXIntMeta":
        # Strict format: MXINT_<elelment_bits>_B<block>_S<scale>, e.g:MXINT_8_B32_S8
        match = re.fullmatch(r"MXINT_(\d+)_B(\d+)_S(\d+)", name)
        if not match:
            raise ValueError(f"Invalid MXIntMeta string: {name} (expected format: MXINT_<element_bits>_B<block>_S<scale>)")

        element_bits = int(match.group(1))
        block_size = int(match.group(2))
        scale_bits = int(match.group(3))

        return cls(
            block_size=block_size,
            scale_bits=scale_bits,
            element_bits=element_bits,
        )
 
@dataclass
class MXIntTensorMeta:
    device: str
    dtype: str
    shape: tuple[int, ...]
    block_dim: int
    meta: MXIntMeta