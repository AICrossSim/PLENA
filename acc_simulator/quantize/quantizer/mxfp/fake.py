import torch
from torch import Tensor

from .meta import MXFPMeta


def extract_mxfp_components(x: Tensor, mxfp_meta: MXFPMeta) -> tuple[Tensor, Tensor]:
    """
    Extracts the scale and element components from a MXFP tensor.

    Args:
        x (Tensor): The input MXFP tensor.
        mxfp_meta (MXFPMeta): The metadata for the MXFP format.
    Returns:
        tuple[Tensor, Tensor]: A tuple containing the scale (shape = [num_blocks, 1]) and element tensors (shape = [num_blocks, block_size]).
    """
    assert x.dtype == torch.bfloat16
    B = mxfp_meta.block_size
    assert x.numel() % B == 0, (
        f"Input tensor size {x.numel()} is not divisible by block size {B}."
    )
    n_blocks = x.numel() // B
    sc_exp_max = 2**mxfp_meta.scale_exp_bits - 1
    el_exp_bits = mxfp_meta.element_exp_bits
    el_exp_max = 2**el_exp_bits - 1
    el_exp_bias = 2 ** (el_exp_bits - 1) - 1
    el_man_bits = mxfp_meta.element_frac_bits
    el_man_max = 2**el_man_bits - 1

    x = x.flatten()
    x = x.reshape(n_blocks, B)  # [n_blocks, B]

    exp = (x.view(torch.int16) & 0x7F80) >> 7  # 0-255
    exp_max = exp.max(dim=1, keepdim=True).values  # [n_blocks, 1]
    flush_to_zero_mask = exp_max == 0
    exp = exp - exp_max
    el_exp = exp + el_exp_bias
    underflow_mask = el_exp < 0
    overflow_mask = el_exp > el_exp_max
    el_exp = torch.where(underflow_mask, 0, el_exp)
    el_exp = torch.where(overflow_mask, el_exp_max, el_exp)

    el_mantissa = x.view(torch.int16) & 0x007F
    el_mantissa = el_mantissa >> (7 - el_man_bits)
    el_mantissa = torch.where(underflow_mask, 0, el_mantissa)
    el_mantissa = torch.where(overflow_mask, el_man_max, el_mantissa)
    sign = x.view(torch.int16) & 0x8000
    sign = sign >> (15 - (el_exp_bits + el_man_bits))
    sign = sign & 2 ** (el_exp_bits + el_man_bits)

    el = sign | (el_exp << el_man_bits) | el_mantissa
    el = torch.where(flush_to_zero_mask, 0, el)
    el = el.view(torch.uint16).to(torch.uint8)

    exp_max = exp_max.clamp(0, sc_exp_max).view(torch.uint16).to(torch.uint8)
    return exp_max, el


def compose_mxfp_tensor(
    shared_scales: Tensor,
    elements: Tensor,
    mxfp_meta: MXFPMeta,
):
    """
    Composes a MXFP tensor from the scale and element components.

    Args:
        shared_scales (Tensor): The shared scales tensor.
        elements (Tensor): The elements tensor.
        mxfp_meta (MXFPMeta): The metadata for the MXFP format.

    Returns:
        Tensor: The composed MXFP tensor.
    """
    assert shared_scales.dtype == torch.uint8
    assert elements.dtype == torch.uint8

    B = mxfp_meta.block_size
    n_blocks = shared_scales.shape[0]
    el_exp_bits = mxfp_meta.element_exp_bits
    el_man_bits = mxfp_meta.element_frac_bits
    el_exp_man_bits = mxfp_meta.element_bits - 1
    el_exp_bias = 2 ** (el_exp_bits - 1) - 1

    exp_max = shared_scales.to(torch.uint16).view(torch.int16)
    exp_max = exp_max.expand(-1, B)  # [n_blocks, B]

    underflow_mask = elements & (2**el_exp_man_bits - 1) == 0
    elements = elements.to(torch.int16)
    sign = elements << (15 - (el_exp_bits + el_man_bits))
    sign = sign & 0x8000
    mantissa = elements & (2**el_man_bits - 1)
    mantissa = mantissa << (7 - el_man_bits)

    el_exp = (elements >> el_man_bits) & (2 ** (el_exp_bits) - 1)
    el_exp = el_exp - el_exp_bias
    exp = exp_max + el_exp
    exp = exp << 7

    dequantized = sign | exp | mantissa
    dequantized = dequantized.view(torch.bfloat16)
    dequantized = torch.where(underflow_mask, 0.0, dequantized)
    dequantized = dequantized.reshape(n_blocks * B)
    return dequantized