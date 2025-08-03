import torch
from torch import Tensor

# from . import fake as mxfp_fake
from .import kernels as int_kernels
from ..mxfp.helpers import flatten_for_quantize, permute_for_dequantize
from .meta import IntMeta, IntTensorMeta
from .fake import extract_int_components as extract_int_components_fake, compose_int_tensor as compose_int_tensor_fake


def extract_int_components(
    tensor: Tensor, block_dim: int, int_meta: IntMeta
) -> tuple[Tensor, Tensor, IntTensorMeta]:
    """
    Extracts the INT components from a tensor.

    .. note::
        The block for exponent sharing is a 1D vector instead of a 2D matrix.

    :param tensor: The input tensor to be quantized.
    :type tensor: torch.Tensor
    :param block_dim: The dimension to group the tensor elements into blocks.
    :type block_dim: int
    :param int_meta: The metadata for the INT format.
    :type int_meta: IntMeta

    :returns: The extracted scales, elements, and tensor metadata.
    :rtype: tuple[torch.Tensor, torch.Tensor, IntTensorMeta]
    """
    device = str(tensor.device)
    ori_shape = tuple(tensor.shape)
    ori_dtype = str(tensor.dtype).removeprefix("torch.")
    ndim = len(ori_shape)
    assert block_dim < ndim and block_dim >= -ndim

    assert device.startswith("cpu") or device.startswith("cuda"), (
        f"Unsupported device: {device}. Only 'cpu' and 'cuda' are supported."
    )
    tensor = tensor.to(torch.bfloat16)
    tensor = flatten_for_quantize(tensor, block_dim)
    if device == "cpu":
        scales, elements = extract_int_components_fake(tensor, int_meta)
    else:
        # scales, elements = mxint_kernels.extract_mxint_components(
        #     tensor, mxint_meta=mxint_meta
        # )
        scales, elements = extract_int_components_fake(tensor, int_meta)
    tensor_meta = IntTensorMeta(
        device=device,
        dtype=ori_dtype,
        shape=ori_shape,
        block_dim=block_dim,
        meta=int_meta,
    )
    return scales, elements, tensor_meta


def compose_int_tensor(
    scales,
    zero,
    elements,
    tensor_meta: IntTensorMeta,
    dtype: torch.dtype | None = None,
) -> Tensor:
    """
    Compose a tensor from INT components.

    :param scales: The shared scales for exponent sharing.
    :type scales: torch.Tensor
    :param elements: The elements of the tensor.
    :type elements: torch.Tensor
    :param tensor_meta: The metadata for the INT tensor.
    :type tensor_meta: IntTensorMeta
    :param dtype: The desired data type of the output tensor, by default None, which uses the dtype from tensor_meta.
    :type dtype: torch.dtype, optional

    :returns: The dequantized tensor.
    :rtype: torch.Tensor
    """
    device = tensor_meta.device
    dtype = getattr(torch, tensor_meta.dtype) if dtype is None else dtype

    if device == "cpu":
        tensor = compose_int_tensor_fake(scales, zero, elements, tensor_meta.meta)
    else:
        # tensor = mxint_kernels.compose_mxint_tensor(
        #     shared_scales=scales,
        #     elements=elements,
        #     mxint_meta=tensor_meta.meta,
        # )
        tensor = compose_int_tensor_fake(scales, zero, elements, tensor_meta.meta)

    tensor = permute_for_dequantize(
        tensor, ori_shape=tensor_meta.shape, block_dim=tensor_meta.block_dim
    )
    tensor = tensor.to(dtype=dtype)
    return tensor


def int_quantizer_sim(
    tensor: Tensor,
    block_dim: int,
    int_meta: IntMeta,
    dtype: torch.dtype | None = None,
) -> Tensor:
    """
    Quantizes and dequantizes a tensor using the INT format.

    :param tensor: The input tensor to be quantized.
    :type tensor: torch.Tensor
    :param block_dim: The dimension to group the tensor elements into blocks.
    :type block_dim: int
    :param int_meta: The metadata for the INT format.
    :type int_meta: IntMeta
    :param dtype: The desired data type of the output tensor, by default None, which uses the dtype from int_meta.

    :returns: The dequantized tensor.
    :rtype: torch.Tensor
    """
    scales, zero, elements, tensor_meta = extract_int_components(
        tensor, block_dim, int_meta
    )
    tensor_dq = compose_int_tensor(scales, zero, elements, tensor_meta, dtype=dtype)
    return tensor_dq