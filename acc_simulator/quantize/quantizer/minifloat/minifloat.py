import torch
from torch import Tensor

from . import fake as minifloat_fake
from .helpers import flatten_for_quantize, permute_for_dequantize
from .meta import MinifloatMeta, MinifloatTensorMeta


def extract_minifloat_components(
    tensor: Tensor, minifloat_meta: MinifloatMeta
) -> MinifloatTensorMeta:
    """
    Extracts the Minifloat components from a tensor.

    .. note::
        The block for exponent sharing is a 1D vector instead of a 2D matrix.

    :param tensor: The input tensor to be quantized.
    :type tensor: torch.Tensor
    :param minifloat_meta: The metadata for the Minifloat format.
    :type minifloat_meta: MinifloatMeta

    :returns: The extracted scales, elements, and tensor metadata.
    :rtype: tuple[torch.Tensor, torch.Tensor, MinifloatTensorMeta]
    """
    device = str(tensor.device)
    ori_shape = tuple(tensor.shape)
    ori_dtype = str(tensor.dtype).removeprefix("torch.")
    ndim = len(ori_shape)

    assert device.startswith("cpu") or device.startswith("cuda"), (
        f"Unsupported device: {device}. Only 'cpu' and 'cuda' are supported."
    )
    tensor = tensor.to(torch.bfloat16)
    if device == "cpu":
        minifloat_fake.extract_minifloat_component(
            tensor, minifloat_meta=minifloat_meta
        )
    else:
        minifloat_fake.extract_minifloat_component(
            tensor, minifloat_meta=minifloat_meta
        )
    tensor_meta = MinifloatTensorMeta(
        device=device,
        dtype=ori_dtype,
        shape=ori_shape,
        meta=minifloat_meta,
    )
    return tensor_meta


def compose_minifloat_tensor(
    scales,
    elements,
    tensor_meta: MinifloatTensorMeta,
    dtype: torch.dtype | None = None,
) -> Tensor:
    """
    Compose a tensor from Minifloat components.

    :param scales: The shared scales for exponent sharing.
    :type scales: torch.Tensor
    :param elements: The elements of the tensor.
    :type elements: torch.Tensor
    :param tensor_meta: The metadata for the Minifloat tensor.
    :type tensor_meta: MinifloatTensorMeta
    :param dtype: The desired data type of the output tensor, by default None, which uses the dtype from tensor_meta.
    :type dtype: torch.dtype, optional

    :returns: The dequantized tensor.
    :rtype: torch.Tensor
    """
    device = tensor_meta.device
    dtype = getattr(torch, tensor_meta.dtype) if dtype is None else dtype

    if device == "cpu":
        tensor = minifloat_fake.compose_minifloat_tensor(
            shared_scales=scales,
            elements=elements,
            minifloat_meta=tensor_meta.meta,
        )
    else:
        tensor = minifloat_fake.compose_minifloat_tensor(
            shared_scales=scales,
            elements=elements,
            minifloat_meta=tensor_meta.meta,
        )

    tensor = permute_for_dequantize(
        tensor, ori_shape=tensor_meta.shape, block_dim=tensor_meta.block_dim
    )
    tensor = tensor.to(dtype=dtype)
    return tensor


def minifloat_quantizer_sim(
    tensor: Tensor,
    block_dim: int,
    minifloat_meta: MinifloatMeta,
    dtype: torch.dtype | None = None,
) -> Tensor:
    """
    Quantizes and dequantizes a tensor using the MXFP format.

    :param tensor: The input tensor to be quantized.
    :type tensor: torch.Tensor
    :param block_dim: The dimension to group the tensor elements into blocks.
    :type block_dim: int
    :param minifloat_meta: The metadata for the Minifloat format.
    :type minifloat_meta: MinifloatMeta
    :param dtype: The desired data type of the output tensor, by default None, which uses the dtype from minifloat_meta.

    :returns: The dequantized tensor.
    :rtype: torch.Tensor
    """
    tensor_meta = extract_minifloat_components(tensor, minifloat_meta)
    tensor_dq = compose_minifloat_tensor(tensor_meta, dtype=dtype)
    return tensor_dq

