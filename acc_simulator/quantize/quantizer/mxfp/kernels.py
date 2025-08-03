import torch
import triton
from torch import Tensor
from triton import language as tl

from .meta import MXFPMeta


def _find_block_max(x: Tensor, block_size: int) -> Tensor:
    B = block_size
    n_blocks = x.numel() // B

    x = x.view(n_blocks, B)
    group_max = x.abs().max(dim=1, keepdim=True).values
    return group_max


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
    el_man_bits: tl.constexpr,
    BLK: tl.constexpr,
):
    # helper constants
    sc_exp_max = 2**sc_exp_bits - 1
    el_exp_max = 2**el_exp_bits - 1
    el_exp_bias = 2 ** (el_exp_bits - 1) - 1
    el_man_max = 2**el_man_bits - 1
    el_sign_mask = 2 ** (el_exp_bits + el_man_bits)

    pid = tl.program_id(axis=0)
    x_offs = pid * BLK + tl.arange(0, BLK)
    block_max_offs = x_offs // block_size

    x_ptrs = x_ptr + x_offs
    block_max_ptrs = block_max_ptr + block_max_offs
    x = tl.load(x_ptrs, mask=x_offs < n_elements, other=0.0)
    block_max = tl.load(block_max_ptrs, mask=block_max_offs < n_blocks, other=0.0)

    x = x.cast(tl.int16, bitcast=True)
    block_max = block_max.cast(tl.int16, bitcast=True)
    exp_max = (block_max & 0x7F80) >> 7  # 0-255
    flush_to_zero_mask = exp_max == 0
    el_exp = (x & 0x7F80) >> 7  # 0-255
    el_exp = (el_exp - exp_max).to(tl.int16)
    el_exp = (el_exp + el_exp_bias).to(tl.int16)
    underflow_mask = el_exp < 0
    overflow_mask = el_exp > el_exp_max
    el_exp = tl.where(underflow_mask, 0, el_exp)
    el_exp = tl.where(underflow_mask, 0, el_exp)
    el_exp = tl.where(overflow_mask, el_exp_max, el_exp)

    el_mantissa = x & 0x007F
    el_mantissa = el_mantissa >> (7 - el_man_bits)
    el_mantissa = tl.where(underflow_mask, 0, el_mantissa)
    el_mantissa = tl.where(overflow_mask, el_man_max, el_mantissa)
    sign = x & -32768  # 0x8000
    sign = sign >> (15 - (el_exp_bits + el_man_bits))
    sign = sign & el_sign_mask

    el = sign | (el_exp << el_man_bits) | el_mantissa
    el = tl.where(flush_to_zero_mask, 0, el)
    el = el.cast(tl.uint8)
    el_ptrs = element_ptr + x_offs
    tl.store(el_ptrs, el, mask=x_offs < n_elements)

    sc = tl.minimum(exp_max, sc_exp_max)
    sc = tl.maximum(sc, 0).cast(tl.uint8)
    sc_ptrs = scale_ptr + block_max_offs
    sc_mask = (block_max_offs < n_blocks) & (x_offs % block_size == 0)
    tl.store(sc_ptrs, sc, mask=sc_mask)


def extract_mxfp_components(
    x: Tensor,
    mxfp_meta: MXFPMeta,
):
    assert x.dtype == torch.bfloat16
    assert x.ndim == 1
    x = x.contiguous()
    n_elements = x.numel()
    B = mxfp_meta.block_size
    assert n_elements % B == 0
    n_groups = n_elements // B
    device = x.device
    scales = torch.empty((n_groups, 1), dtype=torch.uint8, device=device)
    elements = torch.empty((n_groups, B), dtype=torch.uint8, device=device)

    block_max = _find_block_max(x, B)

    def grid(meta):
        return (triton.cdiv(n_elements, meta["BLK"]),)

    # Make Triton Kernel aware of the divce id, avoid ValueError
    with torch.cuda.device(device.index):
        _extract_mxfp_components_kernel[grid](
            x,
            block_max,
            elements,
            scales,
            n_elements=n_elements,
            n_blocks=n_groups,
            block_size=B,
            sc_exp_bits=mxfp_meta.scale_exp_bits,
            el_exp_bits=mxfp_meta.element_exp_bits,
            el_man_bits=mxfp_meta.element_frac_bits,
            BLK=128,
        )

    return scales, elements


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
    el_man_bits: tl.constexpr,
    BLK: tl.constexpr,
):
    # helper constants
    el_exp_man_bits = el_exp_bits + el_man_bits
    el_exp_bias = 2 ** (el_exp_bits - 1) - 1
    el_exp_man_mask = 2 ** (el_exp_bits + el_man_bits) - 1
    el_man_mask = 2**el_man_bits - 1
    el_exp_mask = 2**el_exp_bits - 1

    pid = tl.program_id(axis=0)

    el_offs = pid * BLK + tl.arange(0, BLK)
    sc_offs = el_offs // block_size
    el_ptrs = elements_ptr + el_offs
    sc_ptrs = scales_ptr + sc_offs

    sc = tl.load(sc_ptrs, mask=sc_offs < n_blocks, other=0)
    el = tl.load(el_ptrs, mask=el_offs < n_elements, other=0)

    underflow_mask = (el & el_exp_man_mask) == 0
    exp_max = sc.to(tl.uint16).cast(tl.int16, bitcast=True)
    el = el.to(tl.uint16).cast(tl.int16, bitcast=True)
    el_sign = (el << (15 - el_exp_man_bits)).cast(tl.int16)
    el_sign = el_sign & -32768  # 0x8000
    el_man = (el & el_man_mask).cast(tl.int16)
    el_man = el_man << (7 - el_man_bits)

    el_exp = ((el >> el_man_bits) & el_exp_mask).cast(tl.int16)
    el_exp = (el_exp - el_exp_bias).to(tl.int16)
    el_exp = (el_exp + exp_max).to(tl.int16)
    el_exp = el_exp << 7

    dq = el_sign | el_exp | el_man
    dq = tl.where(underflow_mask, 0, dq)

    dq_ptrs = output_ptr + el_offs
    dq = dq.cast(tl.bfloat16, bitcast=True)
    tl.store(dq_ptrs, dq, mask=el_offs < n_elements)


def compose_mxfp_tensor(
    shared_scales: Tensor,
    elements: Tensor,
    mxfp_meta: MXFPMeta,
) -> Tensor:
    assert shared_scales.dtype == torch.uint8
    assert elements.dtype == torch.uint8

    B = mxfp_meta.block_size
    n_elements = elements.numel()
    n_blocks = shared_scales.shape[0]
    device = shared_scales.device
    elements = elements.contiguous()
    shared_scales = shared_scales.contiguous()

    def grid(meta):
        return (triton.cdiv(n_elements, meta["BLK"]),)

    output = torch.empty(n_elements, dtype=torch.bfloat16, device=device)
    with torch.cuda.device(device.index):
        _compose_mxfp_tensor_kernel[grid](
            shared_scales,
            elements,
            output,
            n_elements=n_elements,
            n_blocks=n_blocks,
            block_size=B,
            sc_exp_bits=mxfp_meta.scale_exp_bits,
            el_exp_bits=mxfp_meta.element_exp_bits,
            el_man_bits=mxfp_meta.element_frac_bits,
            BLK=128,
        )
    return output