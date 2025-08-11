import torch
from torch import Tensor

from . import fake as mxfp_fake
from . import kernels as mxfp_kernels
from .helpers import flatten_for_quantize, permute_for_dequantize
from .meta import MXFPMeta, MXFPTensorMeta


def extract_mxfp_components(
    tensor: Tensor, block_dim: int, mxfp_meta: MXFPMeta, percentile: float = 1.0
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
    :param percentile: The percentile to use for the quantization.
    :type percentile: float, optional

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
            tensor, mxfp_meta=mxfp_meta, percentile=percentile
        )
    else:
        scales, elements = mxfp_fake.extract_mxfp_components(
            tensor, mxfp_meta=mxfp_meta, percentile=percentile
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
    quantile_search: bool = False,
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
        out_dq = torch.zeros_like(tensor)
        qtensor = tensor.flatten()
        B = mxfp_meta.block_size

        qtensor = qtensor.reshape(-1, B)  # [n_blocks, B]
        best_err = torch.full([qtensor.shape[0]], float('inf'), device=tensor.device)
        best_scales, best_elements, tensor_meta = extract_mxfp_components(
            tensor, block_dim, mxfp_meta, percentile=1.0
        )
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
            scale_bias = 2**(mxfp_meta.scale_exp_bits - 1) - 1
            q = elements / 2**(mxfp_meta.scale_exp_bits - 1) * 2**(scales - scale_bias)

            q -= qtensor
            q.abs_()
            q.pow_(2)
            err = torch.sum(q, 1)
            tmp = err < best_err
            if torch.any(tmp):
                best_err[tmp] = err[tmp]
                best_scales[tmp] = scales[tmp]
                best_elements[tmp] = elements[tmp]
    else:
        scales, elements, tensor_meta = extract_mxfp_components(
            tensor, block_dim, mxfp_meta, percentile=1.0
        )
        best_scales = scales
        best_elements = elements
    out_dq = compose_mxfp_tensor(best_scales, best_elements, tensor_meta)
    return out_dq