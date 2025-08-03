import torch
from torch import Tensor

from ..minifloat.fake import (
    compose_minifloat_component,
    extract_minifloat_component,
)
from .meta import MXFPMeta


def extract_mxfp_components(tensor: Tensor, mxfp_meta: MXFPMeta):
    tensor = tensor.float()
    B = mxfp_meta.block_size
    assert tensor.numel() % B == 0

    n_blocks = tensor.numel() // B

    fp32_exp_mask = 0x7F800000

    sc_exp_max = (1 << mxfp_meta.scale_exp_bits) - 1
    sc_exp_min = 0
    sc_exp_bias = (1 << (mxfp_meta.scale_exp_bits - 1)) - 1
    sc_exp_max_biased = sc_exp_max - sc_exp_bias
    sc_exp_min_biased = sc_exp_min - sc_exp_bias

    el_exp_max = (
        (1 << mxfp_meta.element_exp_bits) - 1
        if mxfp_meta.element_is_finite
        else (1 << mxfp_meta.element_exp_bits) - 2
    )
    el_exp_bias = (1 << (mxfp_meta.element_exp_bits - 1)) - 1
    el_exp_max_biased = el_exp_max - el_exp_bias

    tensor = tensor.flatten()
    tensor = tensor.reshape(n_blocks, B)

    x_int32 = tensor.view(torch.int32)
    # flush subnormal to zero
    flush_to_zero = (x_int32 & fp32_exp_mask) == 0
    # tensor = torch.where(flush_to_zero, 0.0, tensor)
    # int32, [n_blocks, 1]
    shared_exp = tensor.abs().max(dim=1, keepdim=True).values
    shared_exp = shared_exp.log2().floor().to(torch.int32)
    shared_exp -= el_exp_max_biased
    shared_exp = shared_exp.clamp(sc_exp_min_biased, sc_exp_max_biased)
    scales_uint = shared_exp + sc_exp_bias
    scales_uint = torch.where(flush_to_zero.all(dim=1, keepdim=True), 0, scales_uint)
    scales_uint = scales_uint.to(torch.uint8)
    # fp32, [n_blocks, 1]
    scales_fp = torch.exp2(shared_exp)

    minifloats = torch.where(flush_to_zero, 0.0, tensor / scales_fp)
    elements = extract_minifloat_component(minifloats, mxfp_meta.element_meta)
    elements = elements.view(torch.uint16)
    elements = elements.to(torch.uint8)

    return scales_uint, elements


def compose_mxfp_tensor(
    scales: Tensor,
    elements: Tensor,
    mxfp_meta: MXFPMeta,
    output_dtype: torch.dtype,
) -> Tensor:
    assert scales.dtype == torch.uint8
    assert elements.dtype == torch.uint8

    sc_exp_bias = (1 << (mxfp_meta.scale_exp_bits - 1)) - 1
    scales_fp = torch.exp2(scales.to(torch.int32) - sc_exp_bias)
    minifloats = compose_minifloat_component(
        elements.to(torch.uint16), mxfp_meta.element_meta, output_dtype=torch.float32
    )

    dequantized = minifloats * scales_fp
    dequantized = dequantized.flatten().to(output_dtype)
    return dequantized
