import torch
from torch import Tensor

from ..utils import device_str, dtype_str, shape_tuple
from . import fake as fp_fake
from . import kernels as fp_kernels
from .meta import MinifloatMeta, MinifloatTensorMeta


def extract_minifloat_component(
    tensor: Tensor, minifloat_meta: MinifloatMeta
) -> tuple[Tensor, MinifloatTensorMeta]:
    """
    Extract the minifloat component from a tensor.

    :param tensor: The input tensor to extract minifloat components from.
    :type tensor: torch.Tensor
    :param minifloat_meta: The metadata for the minifloat format.
    :type minifloat_meta: MinifloatMeta
    :returns: The extracted element (uint16 tensor) and tensor metadata.
    :rtype: tuple[torch.Tensor, MinifloatTensorMeta]
    """
    device = device_str(tensor.device)
    ori_shape = shape_tuple(tensor.shape)
    ori_dtype = dtype_str(tensor.dtype)

    tensor = tensor.to(torch.float32)

    if device.startswith("cuda"):
        element = fp_kernels.extract_minifloat_component(tensor, minifloat_meta)
    else:
        element = fp_fake.extract_minifloat_component(tensor, minifloat_meta)
    tensor_meta = MinifloatTensorMeta(
        device=device, dtype=ori_dtype, shape=ori_shape, meta=minifloat_meta
    )
    return element, tensor_meta


def compose_minifloat_component(
    element: Tensor,
    tensor_meta: MinifloatTensorMeta,
    output_dtype: torch.dtype | None = None,
) -> Tensor:
    """
    Compose a tensor from minifloat components.
    :param element: The element of the minifloat tensor.
    :type element: torch.Tensor
    :param tensor_meta: The metadata for the minifloat tensor.
    :type tensor_meta: MinifloatTensorMeta
    :param dtype: The desired data type of the output tensor, by default None, which
        uses the dtype from tensor_meta.
    :type dtype: torch.dtype, optional
    :returns: The dequantized tensor.
    :rtype: torch.Tensor
    """
    device = tensor_meta.device
    output_dtype = (
        getattr(torch, tensor_meta.dtype) if output_dtype is None else output_dtype
    )

    if device.startswith("cuda"):
        tensor = fp_kernels.compose_minifloat_component(
            element, tensor_meta.meta, output_dtype=output_dtype
        )
    else:
        tensor = fp_fake.compose_minifloat_component(
            element, tensor_meta.meta, output_dtype=output_dtype
        )
    return tensor


def minifloat_quantizer_sim(
    tensor: Tensor,
    minifloat_meta: MinifloatMeta,
    output_dtype: torch.dtype | None = None,
) -> Tensor:
    """
    Quantize and dequantize a tensor using minifloat format.

    :param tensor: The input tensor to quantize and dequantize.
    :type tensor: torch.Tensor
    :param minifloat_meta: The metadata for the minifloat format.
    :type minifloat_meta: MinifloatMeta
    :param output_dtype: The desired data type of the output tensor, by default None, which uses the dtype from tensor_meta.
    :type dtype: torch.dtype, optional
    :returns: The dequantized tensor.
    :rtype: torch.Tensor
    """
    element, tensor_meta = extract_minifloat_component(tensor, minifloat_meta)
    return compose_minifloat_component(element, tensor_meta, output_dtype=output_dtype)
