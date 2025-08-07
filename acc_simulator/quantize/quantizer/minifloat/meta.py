import functools
import re
from dataclasses import dataclass

import torch

from ..utils import device_str, dtype_str, shape_tuple


def _calc_max_normal(exp_bits: int, frac_bits: int, is_finite: bool):
    exp_max = (1 << exp_bits) - 1 if is_finite else (1 << exp_bits) - 2
    exp_bias = (1 << (exp_bits - 1)) - 1
    exp_max -= exp_bias
    frac_max = (1 << frac_bits) - 1
    frac_max = 1 + frac_max / (1 << frac_bits)
    max_normal = 2**exp_max * frac_max
    return max_normal


def _calc_min_normal(exp_bits: int, frac_bits: int):
    exp_min = 1
    exp_bias = (1 << (exp_bits - 1)) - 1
    exp_min -= exp_bias
    frac_min = 1
    min_normal = 2**exp_min * frac_min
    return min_normal


def _calc_max_subnormal(exp_bits: int, frac_bits: int):
    exp_max = 1
    exp_bias = (1 << (exp_bits - 1)) - 1
    exp_max -= exp_bias
    frac_max = (1 << frac_bits) - 1
    frac_max = frac_max / (1 << frac_bits)
    max_subnormal = 2**exp_max * frac_max
    return max_subnormal


def _calc_min_subnormal(exp_bits: int, frac_bits: int):
    exp_min = 1
    exp_bias = (1 << (exp_bits - 1)) - 1
    exp_min -= exp_bias
    frac_min = 1 / (1 << frac_bits)
    min_subnormal = 2**exp_min * frac_min
    return min_subnormal


@dataclass(frozen=True)
class MinifloatMeta:
    """Metadata for minifloat types.

    Args:
        exp_bits (int): Number of exponent bits.
        frac_bits (int): Number of fraction bits.
        is_finite (bool): Whether the minifloat type is finite.

    The sum of `exp_bits` and `frac_bits` must be less than 16 to fit in a 16-bit representation.
    """

    exp_bits: int
    frac_bits: int
    is_finite: bool
    tag: str = ""

    def __post_init__(self):
        assert self.exp_bits > 0
        assert self.frac_bits > 0
        assert self.exp_bits + self.frac_bits < 16

    @functools.cached_property
    def n_bits(self) -> int:
        return self.exp_bits + self.frac_bits + 1

    @functools.cached_property
    def max_normal(self) -> float:
        return _calc_max_normal(self.exp_bits, self.frac_bits, self.is_finite)

    @functools.cached_property
    def min_normal(self) -> float:
        return _calc_min_normal(self.exp_bits, self.frac_bits)

    @functools.cached_property
    def max_subnormal(self) -> float:
        return _calc_max_subnormal(self.exp_bits, self.frac_bits)

    @functools.cached_property
    def min_subnormal(self) -> float:
        return _calc_min_subnormal(self.exp_bits, self.frac_bits)

    @classmethod
    def from_string(cls, config: str) -> "MinifloatMeta":
        """
        Parse strings like:
        - FP_E4M3           → finite=True
        - FP_E4M3_fn        → finite=True
        - FP_E4M3_inf       → finite=False

        Returns:
            MinifloatMeta
        """
        pattern = r"FP_E(?P<exp>\d+)M(?P<frac>\d+)(?:_(?P<flag>fn|inf))?$"
        match = re.fullmatch(pattern, config)
        
        if not match:
            raise ValueError(
                f"Invalid MinifloatMeta string: '{config}'. "
                "Expected format: FP_E<exp>M<frac>[_fn|_inf]"
            )

        exp_bits = int(match.group("exp"))
        frac_bits = int(match.group("frac"))
        flag = match.group("flag")

        is_finite = True if flag is None or flag == "fn" else False
        tag = config

        return cls(
            exp_bits=exp_bits, 
            frac_bits=frac_bits, 
            is_finite=is_finite, 
            tag=tag
        )

# fmt: off
FP8_E4M3_fn = MinifloatMeta(exp_bits=4, frac_bits=3, is_finite=True, tag="FP8_E4M3_fn")
FP8_E5M2_fn = MinifloatMeta(exp_bits=5, frac_bits=2, is_finite=True, tag="FP8_E5M2_fn")
FP6_E2M3_fn = MinifloatMeta(exp_bits=2, frac_bits=3, is_finite=True, tag="FP6_E2M3_fn")
FP6_E3M2_fn = MinifloatMeta(exp_bits=3, frac_bits=2, is_finite=True, tag="FP6_E3M2_fn")
FP4_E2M1_fn = MinifloatMeta(exp_bits=2, frac_bits=1, is_finite=True, tag="FP4_E2M1_fn")
# fmt: on


@dataclass
class MinifloatTensorMeta:
    device: str
    dtype: str
    shape: tuple[int, ...]
    meta: MinifloatMeta

    def __post_init__(self):
        super().__setattr__("device", device_str(self.device))
        super().__setattr__("dtype", dtype_str(self.dtype))
        super().__setattr__("shape", shape_tuple(self.shape))

    def create(
        self,
        device: str | torch.device | None = None,
        dtype: str | torch.dtype | None = None,
        shape: tuple[int, ...] | torch.Size | None = None,
        meta: MinifloatMeta | None = None,
    ) -> "MinifloatTensorMeta":
        device = self.device if device is None else device_str(device)
        dtype = self.dtype if dtype is None else dtype_str(dtype)
        shape = self.shape if shape is None else shape_tuple(shape)
        meta = self.meta if meta is None else meta
        return MinifloatTensorMeta(device=device, dtype=dtype, shape=shape, meta=meta)
