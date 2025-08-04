import torch
import triton
from torch import Tensor
from triton import language as tl

from .meta import MXIntMeta


def _find_block_max(x: Tensor, block_size: int) -> Tensor:
    B = block_size
    n_blocks = x.numel() // B

    x = x.view(n_blocks, B)
    group_max = x.abs().max(dim=1, keepdim=True).values
    return group_max

@triton.jit
def _extract_int_components_kernel(
    x_ptr,
    block_max_ptr,
    element_ptr,
    scale_ptr,
    n_elements: int,
    n_blocks: int,
    block_size: tl.constexpr,
    sc_bits: tl.constexpr,
    el_bits: tl.constexpr,
    BLK: tl.constexpr,
):
    # helper constants
    sc_max = 2**sc_bits - 1
    bf16_exp_max = 2**8 - 2 # 1 bit for inf

    pid = tl.program_id(axis=0)
    x_offs = pid * BLK + tl.arange(0, BLK)
    block_max_offs = x_offs // block_size

    x_ptrs = x_ptr + x_offs
    block_max_ptrs = block_max_ptr + block_max_offs
    x = tl.load(x_ptrs, mask=x_offs < n_elements, other=0.0)
    block_max = tl.load(block_max_ptrs, mask=block_max_offs < n_blocks, other=0.0)

    x = x.cast(tl.uint16, bitcast=True)
    block_max = block_max.cast(tl.int16, bitcast=True)
    ceil_mask = (x & 0x007F) == 0

    exp_max = (block_max & 0x7F80) >> 7  # 0-255
    exp_max = tl.where(ceil_mask, exp_max, exp_max+1)

    el_exp = (x & 0x7F80) >> 7  # 0-255
    el_exp = (el_exp - exp_max + 127 + el_bits - 1).to(tl.int16)
    underflow_mask = el_exp < 0
    overflow_mask = el_exp > bf16_exp_max
    el_exp = tl.where(underflow_mask, 0, el_exp)
    el_exp = tl.where(overflow_mask, bf16_exp_max, el_exp)

    el = (x & 0x807F) | (el_exp << 7)
    el = el.cast(tl.int16)
    el = el.cast(tl.bfloat16, bitcast=True)
    el = el.cast(tl.int8)

    el_ptrs = element_ptr + x_offs
    tl.store(el_ptrs, el, mask=x_offs < n_elements)

    sc = tl.minimum(exp_max, sc_max)
    sc = tl.maximum(sc, 0).cast(tl.uint8)
    sc_ptrs = scale_ptr + block_max_offs
    sc_mask = (block_max_offs < n_blocks) & (x_offs % block_size == 0)
    tl.store(sc_ptrs, sc, mask=sc_mask)


def extract_mxint_components(
    x: Tensor,
    mxint_meta: MXIntMeta,
):
    assert x.dtype == torch.bfloat16
    assert x.ndim == 1
    x = x.contiguous()
    n_elements = x.numel()
    B = mxint_meta.block_size
    assert n_elements % B == 0
    n_groups = n_elements // B
    device = x.device
    scales = torch.empty((n_groups, 1), dtype=torch.uint8, device=device)
    elements = torch.empty((n_groups, B), dtype=torch.int8, device=device)

    block_max = _find_block_max(x, B)
    def grid(meta):
        return (triton.cdiv(n_elements, meta["BLK"]),)

    # Make Triton Kernel aware of the divce id, avoid ValueError
    with torch.cuda.device(device.index):
        _extract_mxint_components_kernel[grid](
            x,
            block_max,
            elements,
            scales,
            n_elements=n_elements,
            n_blocks=n_groups,
            block_size=B,
            sc_bits=mxint_meta.scale_bits,
            el_bits=mxint_meta.element_bits,
            BLK=128,
        )

    return scales, elements


def compose_mxint_tensor(
    shared_scales: Tensor,
    elements: Tensor,
    mxint_meta: MXIntMeta,
) -> Tensor:
    assert shared_scales.dtype == torch.uint8
    assert elements.dtype == torch.int8

    B = mxint_meta.block_size
    n_elements = elements.numel()
    n_blocks = shared_scales.shape[0]
    device = shared_scales.device
    elements = elements.contiguous()
    shared_scales = shared_scales.contiguous()
    scale_bits = mxint_meta.scale_bits
    element_bits = mxint_meta.element_bits

    scale_bias = 2**(scale_bits - 1) - 1
    signed_scale = (shared_scales - scale_bias).to(torch.int8).to(torch.bfloat16)
    output = elements / 2**(element_bits-1) * 2**signed_scale

    return output