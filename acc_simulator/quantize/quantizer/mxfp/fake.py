import torch
from torch import Tensor

# from quant.quantizer.minifloat import minifloat_denorm_quantizer
from ..minifloat.minifloat_fake import minifloat_denorm_quantizer
from ..minifloat.fake import (
    compose_minifloat_component,
    extract_minifloat_component,
)
from .meta import MXFPMeta


def extract_mxfp_components(x: Tensor, mxfp_meta: MXFPMeta, percentile: float = 1.0):
    assert x.dtype == torch.bfloat16
    B = mxfp_meta.block_size
    assert x.numel() % B == 0, (
        f"Input tensor size {x.numel()} is not divisible by block size {B}."
    )
    n_blocks = x.numel() // B

    x = x.flatten()
    x = x.reshape(n_blocks, B)  # [n_blocks, B]
    per_block_max = x.abs().to(torch.float32).quantile(percentile, dim=1, keepdim=True) + 1e-9
    scales = per_block_max.log2().ceil()
    scales = scales.clamp(min=-2**(mxfp_meta.scale_exp_bits - 1), max=2**(mxfp_meta.scale_exp_bits - 1) - 1)

    q_tensor = x / 2**scales
    per_block_bm_x = minifloat_denorm_quantizer(
        q_tensor,
        width=mxfp_meta.element_frac_bits + mxfp_meta.element_exp_bits + 1,
        exponent_width=mxfp_meta.element_exp_bits,
    )

    return scales, per_block_bm_x


def compose_mxfp_tensor(
    shared_scales: Tensor,
    elements: Tensor,
    mxfp_meta: MXFPMeta,
) -> Tensor:
    dequantized = elements * 2**shared_scales
    dequantized = dequantized.flatten().to(torch.bfloat16)
    return dequantized
