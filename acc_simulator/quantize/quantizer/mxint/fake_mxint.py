import torch
from torch import Tensor

from .meta import MXIntMeta


def extract_mxint_components(x: Tensor, mxint_meta: MXIntMeta, percentile: float = 1.0) -> tuple[Tensor, Tensor]:
    """
    Extracts the scale and element components from a MXFP tensor.

    Args:
        x (Tensor): The input MXFP tensor.
        mxfp_meta (MXFPMeta): The metadata for the MXFP format.
    Returns:
        tuple[Tensor, Tensor]: A tuple containing the scale (shape = [num_blocks, 1]) and element tensors (shape = [num_blocks, block_size]).
    """
    assert x.dtype == torch.bfloat16
    B = mxint_meta.block_size
    assert x.numel() % B == 0, (
        f"Input tensor size {x.numel()} is not divisible by block size {B}."
    )
    n_blocks = x.numel() // B

    x = x.flatten()
    x = x.reshape(n_blocks, B)  # [n_blocks, B]

    x_max = x.abs().to(torch.float32).quantile(percentile, dim=1, keepdim=True)
    scale = x_max.log2().ceil()
    scale_bias = 2**(mxint_meta.scale_bits - 1) - 1
    x = x / 2**scale
    x_mant = x * 2**(mxint_meta.element_bits - 1)
    scale = scale + scale_bias
    scale = scale.clamp(min=0, max=2**mxint_meta.scale_bits-1)
    x_mant = x_mant.round().clamp(min=-2**(mxint_meta.element_bits-1), max=2**(mxint_meta.element_bits-1)-1)

    return scale, x_mant


def compose_mxint_tensor(
    shared_scales: Tensor,
    elements: Tensor,
    mxint_meta: MXIntMeta,
):
    """
    Composes a MXINT tensor from the scale and element components.

    Args:
        shared_scales (Tensor): The shared scales tensor.
        elements (Tensor): The elements tensor.
        mxint_meta (MXIntMeta): The metadata for the MXINT format.

    Returns:
        Tensor: The composed MXINT tensor.
    """
    B = mxint_meta.block_size
    n_blocks = shared_scales.shape[0]
    scale_bias = 2**(mxint_meta.scale_bits - 1) - 1
    return elements / 2**(mxint_meta.element_bits-1) * 2**(shared_scales - scale_bias)