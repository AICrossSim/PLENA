import functools
from dataclasses import dataclass
from typing import Literal
import re

import torch

from ..minifloat.meta import MinifloatMeta
from ..utils import device_str, dtype_str, shape_tuple


@dataclass(frozen=True)
class MXFPMeta:
    block_size: int
    scale_exp_bits: int
    element_exp_bits: int
    element_frac_bits: int
    element_is_finite: bool
    round_mode: Literal["rn", "ru", "rd", "rz"]
    tag: str = ""

    def __post_init__(self):
        # check scale exponent bits
        legal_scale_exp_bits = (8,)
        assert self.scale_exp_bits in legal_scale_exp_bits, (
            f"Invalid exponent bits: {self.scale_exp_bits}. "
            f"Legal values are: {legal_scale_exp_bits}."
        )
        # check element exponent and fraction bits
        legal_element_exp_frac_bits = ((4, 3), (5, 2), (2, 3), (3, 2), (2, 1), (1, 2))
        el_exp_frac = (self.element_exp_bits, self.element_frac_bits)
        assert el_exp_frac in legal_element_exp_frac_bits, (
            f"Invalid element exponent and fraction bits: {self.element_exp_bits}, {self.element_frac_bits}. "
            f"Legal values are: {legal_element_exp_frac_bits}."
        )

    @functools.cached_property
    def element_meta(self) -> MinifloatMeta:
        """Returns the metadata for the element (Minifloat) part of the MXFP format."""
        return MinifloatMeta(
            exp_bits=self.element_exp_bits,
            frac_bits=self.element_frac_bits,
            is_finite=self.element_is_finite,
            round_mode=self.round_mode,
        )
    
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
        element_is_finite = True
        round_mode = "rn"

        return cls(
            block_size=block_size,
            scale_exp_bits=scale_exp_bits,
            element_exp_bits=element_exp_bits,
            element_frac_bits=element_frac_bits,
            element_is_finite=element_is_finite,
            round_mode=round_mode,
        )


@dataclass(frozen=True)
class MXFPTensorMeta:
    device: str
    dtype: str
    shape: tuple[int, ...]
    block_dim: int
    meta: MXFPMeta

    def __post_init__(self):
        super().__setattr__("device", device_str(self.device))
        super().__setattr__("dtype", dtype_str(self.dtype))
        super().__setattr__("shape", shape_tuple(self.shape))

    def create(
        self,
        device: str | torch.device | None = None,
        dtype: str | torch.dtype | None = None,
        shape: tuple[int, ...] | torch.Size | None = None,
        block_dim: int | None = None,
        meta: MXFPMeta | None = None,
    ) -> "MXFPTensorMeta":
        device = self.device if device is None else device_str(device)
        dtype = self.dtype if dtype is None else dtype_str(dtype)
        shape = self.shape if shape is None else shape_tuple(shape)
        block_dim = self.block_dim if block_dim is None else block_dim
        meta = self.meta if meta is None else meta
        return MXFPTensorMeta(
            device=device,
            dtype=dtype,
            shape=shape,
            block_dim=block_dim,
            meta=meta,
        )