import torch
import triton
from torch import Tensor
from triton import language as tl
from triton.language.extra import libdevice

from ...dtype import TORCH_DTYPE_TO_TRITON
from ...manager import KernelManager
from ..meta import MinifloatMeta


def _get_autotune_configs_extract_minifloat_component_kernel():
    block_sizes = [128, 256, 512, 1024]
    stages = [4, 5]
    configs = []
    for bs in block_sizes:
        for s in stages:
            configs.append(triton.Config({"BLK": bs}, num_stages=s))
    return configs


def _get_default_config_extract_minifloat_component_kernel():
    return [triton.Config({"BLK": 256}, num_stages=4)]


@triton.jit
def _extract_minifloat_component_core(
    x,
    exp_bits: tl.constexpr,
    frac_bits: tl.constexpr,
    is_finite: tl.constexpr,
    round_mode: tl.constexpr,
    x_dtype: tl.constexpr,
):
    # constants
    y_exp_bias = (1 << (exp_bits - 1)) - 1
    if is_finite:
        y_exp_max = (1 << exp_bits) - 1
    else:
        y_exp_max = (1 << exp_bits) - 2
    y_exp_max_biased = y_exp_max - y_exp_bias
    y_exp_min = 0
    y_exp_min_biased = y_exp_min - y_exp_bias
    y_frac_max = (1 << frac_bits) - 1
    y_nan_const = (1 << (exp_bits + frac_bits)) - 1
    y_inf_const = y_nan_const - ((1 << frac_bits) - 1)
    y_sign_const = 1 << (exp_bits + frac_bits)

    x = x.to(tl.float32)

    y_sign = x < 0

    x = tl.abs(x)
    x_int32 = x.to(tl.int32, bitcast=True)
    flush_to_zero = (x_int32 & 0x7F800000) == 0
    x = tl.where(flush_to_zero, 0.0, x)
    x_exp = libdevice.ilogb(x)  # [-126, 127]
    x_frac = x_int32 & 0x7FFFFF
    x_frac = x_frac | 0x3F800000
    x_frac = x_frac.to(tl.float32, bitcast=True)
    # this x_frac is now equivalent to the output x_frac in fake's line 28
    x_is_inf = None
    x_is_nan = None
    if not is_finite:
        x_is_inf = libdevice.isinf(x)
        x_is_nan = libdevice.isnan(x)

    y_exp = x_exp
    underflow = y_exp < y_exp_min_biased
    overflow = y_exp > y_exp_max_biased
    y_exp = y_exp + y_exp_bias

    y_frac = x_frac.to(tl.int32, bitcast=True)
    y_frac = y_frac & 0x7FFFFF

    if round_mode == "rz":
        # truncate
        y_frac = y_frac >> (23 - frac_bits)
    else:
        # round
        y_frac_fp = (y_frac >> 8).to(tl.float32)
        div = 1 << (15 - frac_bits)
        y_frac_fp = y_frac_fp / div
        if round_mode == "ru":
            y_frac_fp = libdevice.ceil(y_frac_fp)
        elif round_mode == "rd":
            y_frac_fp = libdevice.floor(y_frac_fp)
        else:
            y_frac_fp = libdevice.round(y_frac_fp)
        y_frac = y_frac_fp.to(tl.int32)

    # subnormal minifloat
    y_is_subnormal = (y_exp == y_exp_min) & (y_frac != 0)
    y_frac = tl.where(y_is_subnormal, (y_frac | (1 << frac_bits)) >> 1, y_frac)
    # underflow -> 0
    y_frac = tl.where(underflow, 0, y_frac)
    y_exp = tl.where(underflow, 0, y_exp)
    # overflow -> max
    y_frac = tl.where(overflow, y_frac_max, y_frac)
    y_exp = tl.where(overflow, y_exp_max, y_exp)
    # flush to zero
    y_frac = tl.where(flush_to_zero, 0, y_frac)
    y_exp = tl.where(flush_to_zero, 0, y_exp)

    y = (y_exp << frac_bits) | y_frac
    y = tl.where(y_sign, y | y_sign_const, y)
    if not is_finite:
        y = tl.where(x_is_nan, y_nan_const, y)
        y = tl.where(x_is_inf, y_inf_const, y)
    y = tl.where(flush_to_zero, 0, y)
    y = y.to(tl.uint16)
    return y


@triton.autotune(
    configs=_get_autotune_configs_extract_minifloat_component_kernel()
    if KernelManager.autotune_is_enabled()
    else _get_default_config_extract_minifloat_component_kernel(),
    key=["exp_bits", "frac_bits", "is_finite", "round_mode", "x_dtype"],
)
@triton.jit
def _extract_minifloat_component_kernel(
    x_ptr,
    element_ptr,
    n_elements: int,
    exp_bits: tl.constexpr,
    frac_bits: tl.constexpr,
    is_finite: tl.constexpr,
    round_mode: tl.constexpr,
    BLK: tl.constexpr,
    x_dtype: tl.constexpr,
):
    pid = tl.program_id(axis=0)
    x_offs = pid * BLK + tl.arange(0, BLK)

    x = tl.load(x_ptr + x_offs, mask=x_offs < n_elements, other=0.0)
    y = _extract_minifloat_component_core(
        x,
        exp_bits=exp_bits,
        frac_bits=frac_bits,
        is_finite=is_finite,
        round_mode=round_mode,
        x_dtype=x_dtype,
    )
    tl.store(element_ptr + x_offs, y, mask=x_offs < n_elements)


def extract_minifloat_component(x: Tensor, minifloat_meta: MinifloatMeta) -> Tensor:
    x = x.contiguous()
    n_elements = x.numel()
    device = x.device

    elements = torch.empty_like(x, dtype=torch.uint16)

    def grid(meta):
        return (triton.cdiv(n_elements, meta["BLK"]),)

    with torch.cuda.device(device.index):
        _extract_minifloat_component_kernel[grid](
            x,
            elements,
            n_elements=n_elements,
            exp_bits=minifloat_meta.exp_bits,
            frac_bits=minifloat_meta.frac_bits,
            is_finite=minifloat_meta.is_finite,
            round_mode=minifloat_meta.round_mode,
            x_dtype=TORCH_DTYPE_TO_TRITON[x.dtype],
        )

    return elements


def _get_autotune_configs_compose_minifloat_component_kernel():
    block_sizes = [128, 256, 512, 1024]
    stages = [4, 5]
    configs = []
    for bs in block_sizes:
        for s in stages:
            configs.append(triton.Config({"BLK": bs}, num_stages=s))
    return configs


def _get_default_config_compose_minifloat_component_kernel():
    return [triton.Config({"BLK": 512}, num_stages=4)]


@triton.jit
def _compose_minifloat_component_core(
    elements,
    exp_bits: tl.constexpr,
    frac_bits: tl.constexpr,
    is_finite: tl.constexpr,
    element_dtype: tl.constexpr,
):
    x_sign_mask = 1 << (exp_bits + frac_bits)
    x_frac_mask = (1 << frac_bits) - 1
    x_exp_bias = (1 << (exp_bits - 1)) - 1

    elements = elements.to(tl.int32)

    y_sign = (elements & x_sign_mask) << (31 - (exp_bits + frac_bits))

    elements = elements & 0x7FFF
    x_exp = (elements >> frac_bits) & ((1 << exp_bits) - 1)
    x_frac = elements & x_frac_mask
    is_subnormal = (x_exp == 0) & (x_frac != 0)
    is_zero = (x_exp == 0) & (x_frac == 0)

    if not is_finite:
        y_is_not_finite = x_exp == ((1 << exp_bits) - 1)
        y_is_inf = y_is_not_finite & (x_frac == 0)
        y_is_nan = y_is_not_finite & (x_frac != 0)

    y_exp = x_exp - x_exp_bias
    y_exp = tl.where(is_subnormal, y_exp + 1, y_exp)
    y_exp = tl.exp2(y_exp.to(tl.float32))
    y_frac = x_frac.to(tl.float32)
    y_frac = y_frac / (1 << frac_bits)
    y_frac = tl.where(is_subnormal, y_frac, y_frac + 1.0)
    y = y_exp * y_frac

    if not is_finite:
        y = tl.where(y_is_nan, float("inf"), y)
        y = tl.where(y_is_inf, float("nan"), y)
    y = tl.where(is_zero, 0.0, y)
    y = tl.where(y_sign != 0, -y, y)
    return y


@triton.autotune(
    configs=_get_autotune_configs_compose_minifloat_component_kernel()
    if KernelManager.autotune_is_enabled()
    else _get_default_config_compose_minifloat_component_kernel(),
    key=["exp_bits", "frac_bits", "is_finite", "element_dtype", "output_dtype"],
)
@triton.jit
def _compose_minifloat_component_kernel(
    elements_ptr,
    output_ptr,
    n_elements: int,
    exp_bits: tl.constexpr,
    frac_bits: tl.constexpr,
    is_finite: tl.constexpr,
    BLK: tl.constexpr,
    element_dtype: tl.constexpr,
    output_dtype: tl.constexpr,
):
    pid = tl.program_id(axis=0)
    x_offs = pid * BLK + tl.arange(0, BLK)

    elements = tl.load(elements_ptr + x_offs, mask=x_offs < n_elements, other=0)
    y = _compose_minifloat_component_core(
        elements,
        exp_bits=exp_bits,
        frac_bits=frac_bits,
        is_finite=is_finite,
        element_dtype=element_dtype,
    )
    y = y.cast(output_dtype)
    tl.store(output_ptr + x_offs, y, mask=x_offs < n_elements)


def compose_minifloat_component(
    elements: Tensor, minifloat_meta: MinifloatMeta, output_dtype: torch.dtype
) -> Tensor:
    elements = elements.contiguous()
    n_elements = elements.numel()
    device = elements.device

    x_dtype = TORCH_DTYPE_TO_TRITON[elements.dtype]
    output = torch.empty_like(elements, dtype=output_dtype)

    def grid(meta):
        return (triton.cdiv(n_elements, meta["BLK"]),)

    with torch.cuda.device(device.index):
        _compose_minifloat_component_kernel[grid](
            elements,
            output,
            n_elements=n_elements,
            exp_bits=minifloat_meta.exp_bits,
            frac_bits=minifloat_meta.frac_bits,
            is_finite=minifloat_meta.is_finite,
            element_dtype=x_dtype,
            output_dtype=TORCH_DTYPE_TO_TRITON[output_dtype],
        )

    return output
