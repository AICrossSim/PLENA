import torch
import triton
from torch import Tensor
from triton import language as tl

from ...dtype import TORCH_DTYPE_TO_TRITON
from ...manager import KernelManager
from ...minifloat.kernels.cast import (
    _compose_minifloat_component_core,
    _extract_minifloat_component_core,
)
from ..meta import MXFPMeta


def _find_block_max(x: Tensor, block_size: int) -> Tensor:
    B = block_size
    n_blocks = x.numel() // B

    x = x.view(n_blocks, B)
    block_max = x.abs().max(dim=1, keepdim=True).values
    return block_max


def _get_default_config_extract_mxfp_components_kernel():
    return [triton.Config({"BLK": 256}, num_stages=4)]


def _get_autotune_configs_extract_mxfp_components_kernel():
    block_sizes = [128, 256, 512, 1024]
    stages = [4, 5]
    configs = []
    for bs in block_sizes:
        for s in stages:
            configs.append(triton.Config({"BLK": bs}, num_stages=s))
    return configs


@triton.autotune(
    configs=_get_autotune_configs_extract_mxfp_components_kernel()
    if KernelManager.autotune_is_enabled()
    else _get_default_config_extract_mxfp_components_kernel(),
    key=[
        "n_elements",
        "n_blocks",
        "block_size",
        "sc_exp_bits",
        "el_exp_bits",
        "el_frac_bits",
        "el_is_finite",
        "round_mode",
        "x_dtype",
    ],
)
@triton.jit
def _extract_mxfp_components_kernel(
    x_ptr,
    block_max_ptr,
    element_ptr,
    scale_ptr,
    n_elements: int,
    n_blocks: int,
    block_size: tl.constexpr,
    sc_exp_bits: tl.constexpr,
    el_exp_bits: tl.constexpr,
    el_frac_bits: tl.constexpr,
    el_is_finite: tl.constexpr,
    round_mode: tl.constexpr,
    BLK: tl.constexpr,
    x_dtype: tl.constexpr,
):
    # helper constants

    fp32_exp_mask = 0x7F800000
    sc_exp_max = (1 << sc_exp_bits) - 1
    sc_exp_min = 0
    sc_exp_bias = (1 << (sc_exp_bits - 1)) - 1
    sc_exp_max_biased = sc_exp_max - sc_exp_bias
    sc_exp_min_biased = sc_exp_min - sc_exp_bias

    el_exp_max = (1 << el_exp_bits) - 1 if el_is_finite else (1 << el_exp_bits) - 2
    el_exp_bias = (1 << (el_exp_bits - 1)) - 1
    el_exp_max_biased = el_exp_max - el_exp_bias

    pid = tl.program_id(axis=0)
    x_offs = pid * BLK + tl.arange(0, BLK)
    block_max_offs = x_offs // block_size

    x_ptrs = x_ptr + x_offs
    x = tl.load(x_ptrs, mask=x_offs < n_elements, other=0.0)
    x_fp32 = x.cast(tl.float32)
    x_int32 = x_fp32.cast(tl.int32, bitcast=True)

    block_max_ptrs = block_max_ptr + block_max_offs
    block_max = tl.load(block_max_ptrs, mask=block_max_offs < n_blocks, other=0.0)
    block_max = block_max.cast(tl.float32)

    flush_to_zero = (x_int32 & fp32_exp_mask) == 0
    shared_exp = block_max.abs().log2().floor()
    shared_exp = shared_exp - el_exp_max_biased
    shared_exp = tl.clamp(shared_exp, sc_exp_min_biased, sc_exp_max_biased)
    scales_uint = shared_exp.to(tl.int32) + sc_exp_bias
    scales_uint = tl.where(flush_to_zero, 0, scales_uint)
    scales_uint = scales_uint.to(tl.uint8)
    # store scales
    sc_ptrs = scale_ptr + block_max_offs
    sc_mask = (block_max_offs < n_blocks) & (x_offs % block_size == 0)
    tl.store(sc_ptrs, scales_uint, mask=sc_mask)

    scales_fp = tl.exp2(shared_exp)
    minifloats = x_fp32 / scales_fp
    minifloats = tl.where(flush_to_zero, 0.0, minifloats)
    elements = _extract_minifloat_component_core(
        minifloats,
        exp_bits=el_exp_bits,
        frac_bits=el_frac_bits,
        is_finite=el_is_finite,
        round_mode=round_mode,
        x_dtype=tl.float32,
    )
    elements = elements.to(tl.uint8)
    # store elements
    el_ptrs = element_ptr + x_offs
    tl.store(el_ptrs, elements, mask=x_offs < n_elements)


def extract_mxfp_components(x: Tensor, mxfp_meta: MXFPMeta) -> tuple[Tensor, Tensor]:
    assert x.ndim == 1
    x = x.contiguous()
    n_elements = x.numel()
    block_size = mxfp_meta.block_size
    assert n_elements % block_size == 0
    n_groups = n_elements // block_size
    device = x.device

    scales = torch.empty((n_groups, 1), dtype=torch.uint8, device=device)
    elements = torch.empty((n_groups, block_size), dtype=torch.uint8, device=device)

    block_max = _find_block_max(x, block_size=block_size).float()

    def grid(meta):
        return (triton.cdiv(n_elements, meta["BLK"]),)

    with torch.cuda.device(device.index):
        _extract_mxfp_components_kernel[grid](
            x,
            block_max,
            elements,
            scales,
            n_elements=n_elements,
            n_blocks=n_groups,
            block_size=block_size,
            sc_exp_bits=mxfp_meta.scale_exp_bits,
            el_exp_bits=mxfp_meta.element_exp_bits,
            el_frac_bits=mxfp_meta.element_frac_bits,
            el_is_finite=mxfp_meta.element_is_finite,
            round_mode=mxfp_meta.round_mode,
            x_dtype=TORCH_DTYPE_TO_TRITON[x.dtype],
        )

    return scales, elements


def _get_default_config_compose_mxfp_tensor_kernel():
    return [triton.Config({"BLK": 512}, num_stages=4)]


def _get_autotune_configs_compose_mxfp_tensor_kernel():
    block_sizes = [128, 256, 512, 1024]
    stages = [4, 5]
    configs = []
    for bs in block_sizes:
        for s in stages:
            configs.append(triton.Config({"BLK": bs}, num_stages=s))
    return configs


@triton.autotune(
    configs=_get_autotune_configs_compose_mxfp_tensor_kernel()
    if KernelManager.autotune_is_enabled()
    else _get_default_config_compose_mxfp_tensor_kernel(),
    key=[
        "n_elements",
        "n_blocks",
        "block_size",
        "sc_exp_bits",
        "el_exp_bits",
        "el_frac_bits",
        "el_is_finite",
        "element_dtype",
        "output_dtype",
    ],
)
@triton.jit
def _compose_mxfp_tensor_kernel(
    scales_ptr,
    elements_ptr,
    output_ptr,
    n_elements: int,
    n_blocks: int,
    block_size: tl.constexpr,
    sc_exp_bits: tl.constexpr,
    el_exp_bits: tl.constexpr,
    el_frac_bits: tl.constexpr,
    el_is_finite: tl.constexpr,
    BLK: tl.constexpr,
    element_dtype: tl.constexpr,
    output_dtype: tl.constexpr,
):
    sc_exp_bias = (1 << (sc_exp_bits - 1)) - 1

    pid = tl.program_id(axis=0)

    el_offs = pid * BLK + tl.arange(0, BLK)
    sc_offs = el_offs // block_size
    el_ptrs = elements_ptr + el_offs
    sc_ptrs = scales_ptr + sc_offs

    sc = tl.load(sc_ptrs, mask=sc_offs < n_blocks, other=0)
    el = tl.load(el_ptrs, mask=el_offs < n_elements, other=0)

    scales_fp = sc.cast(tl.float32)
    scales_fp = tl.exp2(scales_fp - sc_exp_bias)
    minifloats = _compose_minifloat_component_core(
        el,
        exp_bits=el_exp_bits,
        frac_bits=el_frac_bits,
        is_finite=el_is_finite,
        element_dtype=element_dtype,
    )
    minifloats = minifloats * scales_fp
    minifloats = minifloats.to(output_dtype)

    out_ptrs = output_ptr + el_offs
    tl.store(out_ptrs, minifloats, mask=el_offs < n_elements)


def compose_mxfp_tensor(
    scales: Tensor,
    elements: Tensor,
    mxfp_meta: MXFPMeta,
    output_dtype: torch.dtype,
) -> Tensor:
    assert scales.dtype == torch.uint8
    assert elements.dtype == torch.uint8

    n_elements = elements.numel()
    block_size = mxfp_meta.block_size
    n_blocks = n_elements // block_size

    device = elements.device
    output = torch.empty((n_elements,), dtype=output_dtype, device=device)

    def grid(meta):
        return (triton.cdiv(n_elements, meta["BLK"]),)

    with torch.cuda.device(device.index):
        _compose_mxfp_tensor_kernel[grid](
            scales,
            elements,
            output,
            n_elements=n_elements,
            n_blocks=n_blocks,
            block_size=block_size,
            sc_exp_bits=mxfp_meta.scale_exp_bits,
            el_exp_bits=mxfp_meta.element_exp_bits,
            el_frac_bits=mxfp_meta.element_frac_bits,
            el_is_finite=mxfp_meta.element_is_finite,
            element_dtype=TORCH_DTYPE_TO_TRITON[elements.dtype],
            output_dtype=TORCH_DTYPE_TO_TRITON[output.dtype],
        )

    return output
