import functools
import re
from dataclasses import dataclass

import torch

from mase_triton.minifloat.meta import MinifloatMeta
from ..utils import device_str, dtype_str, shape_tuple


@dataclass(frozen=True)
class MXFPMeta:
    block_size: int
    scale_exp_bits: int
    element_exp_bits: int
    element_frac_bits: int
    element_is_finite: bool = True
    tag: str = ""

    def __post_init__(self):
        # check scale exponent bits
        legal_scale_exp_bits = (8,)
        assert self.scale_exp_bits in legal_scale_exp_bits, (
            f"Invalid exponent bits: {self.scale_exp_bits}. "
            f"Legal values are: {legal_scale_exp_bits}."
        )
        # check element exponent and fraction bits
        legal_element_exp_frac_bits = ((4, 3), (5, 2), (2, 3), (3, 2), (2, 1))
        el_exp_frac = (self.element_exp_bits, self.element_frac_bits)
        assert el_exp_frac in legal_element_exp_frac_bits, (
            f"Invalid element exponent and fraction bits: {self.element_exp_bits}, {self.element_frac_bits}. "
            f"Legal values are: {legal_element_exp_frac_bits}."
        )

    @classmethod
    def from_string(cls, config: str) -> "MXFPMeta":
        """
        Parse strings like:
        - MXFP_E4M3_B32_S8
        - MXFP_E4M3_B32_S8_fn
        - MXFP_E4M3_B32_S8_inf

        Format:
            MXFP_E<exp>M<frac>_B<block>_S<scale>[_fn|_inf]

        Returns:
            MXFPMeta instance
        """
        pattern = r"MXFP_E(?P<exp>\d+)M(?P<frac>\d+)_B(?P<block>\d+)_S(?P<scale>\d+)(?:_(?P<finite>fn|inf))?$"
        match = re.fullmatch(pattern, config, flags=re.IGNORECASE)
        if not match:
            raise ValueError(
                f"Invalid MXFPMeta string: {config}. "
                "Expected format: MXFP_E<exp>M<frac>_B<block>_S<scale>[_fn|_inf]"
            )

        element_exp_bits = int(match.group("exp"))
        element_frac_bits = int(match.group("frac"))
        block_size = int(match.group("block"))
        scale_exp_bits = int(match.group("scale"))
        finite_flag = match.group("finite")
        element_is_finite = True if finite_flag is None or finite_flag.lower() == "fn" else False

        return cls(
            block_size=block_size,
            scale_exp_bits=scale_exp_bits,
            element_exp_bits=element_exp_bits,
            element_frac_bits=element_frac_bits,
            element_is_finite=element_is_finite,
            tag=config,
        )

    @functools.cached_property
    def element_meta(self) -> MinifloatMeta:
        """Returns the metadata for the element (Minifloat) part of the MXFP format."""
        return MinifloatMeta(
            exp_bits=self.element_exp_bits,
            frac_bits=self.element_frac_bits,
            is_finite=self.element_is_finite,
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


MXFP8_E4M3_fn = MXFPMeta(
    block_size=32,
    scale_exp_bits=8,
    element_exp_bits=4,
    element_frac_bits=3,
    element_is_finite=True,
    tag="MXFP8_E4M3_fn",
)
MXFP8_E5M2_fn = MXFPMeta(
    block_size=32,
    scale_exp_bits=8,
    element_exp_bits=5,
    element_frac_bits=2,
    element_is_finite=True,
    tag="MXFP8_E5M2_fn",
)
OCP_MXFP6_E2M3 = MXFPMeta(
    block_size=32,
    scale_exp_bits=8,
    element_exp_bits=2,
    element_frac_bits=3,
    element_is_finite=True,
    tag="OCP_MXFP6_E2M3",
)
OCP_MXFP6_E3M2 = MXFPMeta(
    block_size=32,
    scale_exp_bits=8,
    element_exp_bits=3,
    element_frac_bits=2,
    element_is_finite=True,
    tag="OCP_MXFP6_E3M2",
)
OCP_MXFP4_E2M1 = MXFPMeta(
    block_size=32,
    scale_exp_bits=8,
    element_exp_bits=2,
    element_frac_bits=1,
    element_is_finite=True,
    tag="OCP_MXFP4_E2M1",
)
