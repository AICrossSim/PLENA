import torch
from torch import Tensor

from . import fake as mxfp_fake
from . import kernels as mxfp_kernels
from .helpers import flatten_for_quantize, permute_for_dequantize
from .meta import MXFPMeta, MXFPTensorMeta


def extract_mxfp_components(
    tensor: Tensor, block_dim: int, mxfp_meta: MXFPMeta
) -> tuple[Tensor, Tensor, MXFPTensorMeta]:
    """
    Extracts the MXFP components from a tensor.

    .. note::
        The block for exponent sharing is a 1D vector instead of a 2D matrix.

    :param tensor: The input tensor to be quantized.
    :type tensor: torch.Tensor
    :param block_dim: The dimension to group the tensor elements into blocks.
    :type block_dim: int
    :param mxfp_meta: The metadata for the MXFP format.
    :type mxfp_meta: MXFPMeta

    :returns: The extracted scales, elements, and tensor metadata.
    :rtype: tuple[torch.Tensor, torch.Tensor, MXFPTensorMeta]
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
        scales, elements = mxfp_fake.extract_mxfp_components(
            tensor, mxfp_meta=mxfp_meta
        )
    else:
        scales, elements = mxfp_fake.extract_mxfp_components(
            tensor, mxfp_meta=mxfp_meta
        )
    tensor_meta = MXFPTensorMeta(
        device=device,
        dtype=ori_dtype,
        shape=ori_shape,
        block_dim=block_dim,
        meta=mxfp_meta,
    )
    return scales, elements, tensor_meta


def compose_mxfp_tensor(
    scales,
    elements,
    tensor_meta: MXFPTensorMeta,
    dtype: torch.dtype | None = None,
) -> Tensor:
    """
    Compose a tensor from MXFP components.

    :param scales: The shared scales for exponent sharing.
    :type scales: torch.Tensor
    :param elements: The elements of the tensor.
    :type elements: torch.Tensor
    :param tensor_meta: The metadata for the MXFP tensor.
    :type tensor_meta: MXFPTensorMeta
    :param dtype: The desired data type of the output tensor, by default None, which uses the dtype from tensor_meta.
    :type dtype: torch.dtype, optional

    :returns: The dequantized tensor.
    :rtype: torch.Tensor
    """
    device = tensor_meta.device
    dtype = getattr(torch, tensor_meta.dtype) if dtype is None else dtype

    if device == "cpu":
        tensor = mxfp_fake.compose_mxfp_tensor(
            shared_scales=scales,
            elements=elements,
            mxfp_meta=tensor_meta.meta,
        )
    else:
        tensor = mxfp_fake.compose_mxfp_tensor(
            shared_scales=scales,
            elements=elements,
            mxfp_meta=tensor_meta.meta,
        )

    tensor = permute_for_dequantize(
        tensor, ori_shape=tensor_meta.shape, block_dim=tensor_meta.block_dim
    )
    tensor = tensor.to(dtype=dtype)
    return tensor


from cfl_tools.debugger import _get_similarity
def mxfp_quantizer_sim(
    tensor: Tensor,
    block_dim: int,
    mxfp_meta: MXFPMeta,
    dtype: torch.dtype | None = None,
    quantile_search: bool = True,
) -> Tensor:
    """
    Quantizes and dequantizes a tensor using the MXFP format.

    :param tensor: The input tensor to be quantized.
    :type tensor: torch.Tensor
    :param block_dim: The dimension to group the tensor elements into blocks.
    :type block_dim: int
    :param mxfp_meta: The metadata for the MXFP format.
    :type mxfp_meta: MXFPMeta
    :param dtype: The desired data type of the output tensor, by default None, which uses the dtype from mxfp_meta.

    :returns: The dequantized tensor.
    :rtype: torch.Tensor
    """

    if quantile_search:
        percentiles = [
            1.0,
            0.999, 0.998, 0.997, 0.995, 0.993, 0.99,
            0.98, 0.97, 0.96, 0.95,
            0.93, 0.91, 0.90,
            0.87, 0.85, 0.83, 0.80,
            0.75, 0.70, 0.65, 0.60, 0.55, 0.50
        ]
        for percentile in percentiles:
            scales, elements, tensor_meta = extract_mxfp_components(
                tensor, block_dim, mxfp_meta, percentile=percentile
            )
            tensor_dq = compose_mxfp_tensor(scales, elements, tensor_meta, dtype=dtype)
            similarity = _get_similarity(tensor, tensor_dq, metric="l2norm").mean().abs()
            out_dq = tensor_dq if similarity < min_similarity else out_dq
            min_similarity = torch.minimum(min_similarity, similarity)
    else:
        scales, elements, tensor_meta = extract_mxfp_components(
            tensor, block_dim, mxfp_meta, percentile=1.0
        )
        out_dq = compose_mxfp_tensor(scales, elements, tensor_meta, dtype=dtype)
    scales, elements, tensor_meta = extract_mxfp_components(
        tensor, block_dim, mxfp_meta
    )
    tensor_dq = compose_mxfp_tensor(scales, elements, tensor_meta, dtype=dtype)
    return tensor_dq