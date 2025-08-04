import torch
from torch import Tensor

from .meta import IntMeta


def extract_int_components(x: Tensor, int_meta: IntMeta) -> tuple[Tensor, Tensor]:
    """
    Extracts the scale and element components from a INT tensor.

    Args:
        x (Tensor): The input INT tensor.
        int_meta (IntMeta): The metadata for the INT format.
    Returns:
        tuple[Tensor, Tensor]: A tuple containing the scale (shape = [num_blocks, 1]) and element tensors (shape = [num_blocks, block_size]).
    """
    assert x.dtype == torch.bfloat16
    B = int_meta.block_size
    assert x.numel() % B == 0, (
        f"Input tensor size {x.numel()} is not divisible by block size {B}."
    )
    n_blocks = x.numel() // B

    x = x.flatten()
    x = x.reshape(n_blocks, B)  # [n_blocks, B]

    zero = x.mean(dim=1, keepdim=True)
    qx = x - zero
    scale = qx.abs().max(dim=1, keepdim=True).values
    qx = qx / scale

    x_mant = qx * 2**(int_meta.element_bits - 1)

    x_mant = x_mant.round().clamp(min=-2**(int_meta.element_bits-1), max=2**(int_meta.element_bits-1)-1)

    return scale, zero, x_mant


def compose_int_tensor(
    shared_scales: Tensor,
    zero: Tensor,
    elements: Tensor,
    int_meta: IntMeta,
):
    """
    Composes a INT tensor from the scale and element components.

    Args:
        shared_scales (Tensor): The shared scales tensor.
        elements (Tensor): The elements tensor.
        int_meta (IntMeta): The metadata for the INT format.

    Returns:
        Tensor: The composed INT tensor.
    """
    return elements / 2**(int_meta.element_bits-1) * 2**(shared_scales) + zero