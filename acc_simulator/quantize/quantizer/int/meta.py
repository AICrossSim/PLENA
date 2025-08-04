from dataclasses import dataclass
import re

@dataclass
class IntMeta:
    block_size: int
    element_bits: int

    @classmethod
    def from_string(cls, name: str) -> "IntMeta":
        # Strict format: INT_<elelment_bits>_B<block>, e.g:INT_8_B32
        match = re.fullmatch(r"INT_(\d+)_B(\d+)", name)
        if not match:
            raise ValueError(f"Invalid IntMeta string: {name} (expected format: INT_<element_bits>_B<block>)")

        element_bits = int(match.group(1))
        block_size = int(match.group(2))

        return cls(
            block_size=block_size,
            element_bits=element_bits,
        )
 
@dataclass
class IntTensorMeta:
    device: str
    dtype: str
    shape: tuple[int, ...]
    block_dim: int
    meta: IntMeta