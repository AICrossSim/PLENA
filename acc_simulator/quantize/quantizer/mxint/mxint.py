import torch
from torch import Tensor

# from . import fake as mxfp_fake
from .import kernels as mxint_kernels
from ..mxfp.helpers import flatten_for_quantize, permute_for_dequantize
from .meta import MXIntMeta, MXIntTensorMeta
from .fake import extract_mxint_components as extract_mxint_components_fake, compose_mxint_tensor as compose_mxint_tensor_fake


def extract_mxint_components(
    tensor: Tensor, block_dim: int, mxint_meta: MXIntMeta, percentile: float = 1.0
) -> tuple[Tensor, Tensor, MXIntTensorMeta]:
    """
    Extracts the MXINT components from a tensor.

    .. note::
        The block for exponent sharing is a 1D vector instead of a 2D matrix.

    :param tensor: The input tensor to be quantized.
    :type tensor: torch.Tensor
    :param block_dim: The dimension to group the tensor elements into blocks.
    :type block_dim: int
    :param mxint_meta: The metadata for the MXINT format.
    :type mxint_meta: MXIntMeta

    :returns: The extracted scales, elements, and tensor metadata.
    :rtype: tuple[torch.Tensor, torch.Tensor, MXIntTensorMeta]
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
        scales, elements = extract_mxint_components_fake(tensor, mxint_meta, percentile=percentile)
    else:
        # scales, elements = mxint_kernels.extract_mxint_components(
        #     tensor, mxint_meta=mxint_meta
        # )
        scales, elements = extract_mxint_components_fake(tensor, mxint_meta, percentile=percentile)
    tensor_meta = MXIntTensorMeta(
        device=device,
        dtype=ori_dtype,
        shape=ori_shape,
        block_dim=block_dim,
        meta=mxint_meta,
    )
    return scales, elements, tensor_meta


def compose_mxint_tensor(
    scales,
    elements,
    tensor_meta: MXIntTensorMeta,
    dtype: torch.dtype | None = None,
) -> Tensor:
    """
    Compose a tensor from MXINT components.

    :param scales: The shared scales for exponent sharing.
    :type scales: torch.Tensor
    :param elements: The elements of the tensor.
    :type elements: torch.Tensor
    :param tensor_meta: The metadata for the MXINT tensor.
    :type tensor_meta: MXIntTensorMeta
    :param dtype: The desired data type of the output tensor, by default None, which uses the dtype from tensor_meta.
    :type dtype: torch.dtype, optional

    :returns: The dequantized tensor.
    :rtype: torch.Tensor
    """
    device = tensor_meta.device
    dtype = getattr(torch, tensor_meta.dtype) if dtype is None else dtype

    if device == "cpu":
        tensor = compose_mxint_tensor_fake(scales, elements, tensor_meta.meta)
    else:
        # tensor = mxint_kernels.compose_mxint_tensor(
        #     shared_scales=scales,
        #     elements=elements,
        #     mxint_meta=tensor_meta.meta,
        # )
        tensor = compose_mxint_tensor_fake(scales, elements, tensor_meta.meta)

    tensor = permute_for_dequantize(
        tensor, ori_shape=tensor_meta.shape, block_dim=tensor_meta.block_dim
    )
    tensor = tensor.to(dtype=dtype)
    return tensor


def mxint_quantizer_sim(
    tensor: Tensor,
    block_dim: int,
    mxint_meta: MXIntMeta,
    dtype: torch.dtype | None = None,
    quantile_search: bool = True,
) -> Tensor:
    """
    Quantizes and dequantizes a tensor using the MXINT format.

    :param tensor: The input tensor to be quantized.
    :type tensor: torch.Tensor
    :param block_dim: The dimension to group the tensor elements into blocks.
    :type block_dim: int
    :param mxint_meta: The metadata for the MXINT format.
    :type mxint_meta: MXIntMeta
    :param dtype: The desired data type of the output tensor, by default None, which uses the dtype from mxint_meta.

    :returns: The dequantized tensor.
    :rtype: torch.Tensor
    """
    from cfl_tools.debugger import _get_similarity
    min_similarity = torch.tensor(float("inf"), device=tensor.device)
    out_dq = torch.zeros_like(tensor)
    if quantile_search:
        for percentile in [1.0, 0.99, 0.95, 0.90, 0.80, 0.70, 0.60, 0.50]:
            scales, elements, tensor_meta = extract_mxint_components(
                tensor, block_dim, mxint_meta, percentile=percentile
            )
            tensor_dq = compose_mxint_tensor(scales, elements, tensor_meta, dtype=dtype)
            similarity = _get_similarity(tensor, tensor_dq, metric="l2norm").mean().abs()
            out_dq = tensor_dq if similarity < min_similarity else out_dq
            min_similarity = torch.minimum(min_similarity, similarity)
    else:
        scales, elements, tensor_meta = extract_mxint_components(
            tensor, block_dim, mxint_meta, percentile=1.0
        )
        out_dq = compose_mxint_tensor(scales, elements, tensor_meta, dtype=dtype)
    return out_dq