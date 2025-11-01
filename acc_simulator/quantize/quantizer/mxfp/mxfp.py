import torch
from torch import Tensor

from tqdm import tqdm
from ..utils import device_str, dtype_str, shape_tuple
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

    :returns: The extracted scales, elements, and tensor metadata.
    :rtype: tuple[torch.Tensor, torch.Tensor, MXFPTensorMeta]
    """
    device = device_str(tensor.device)
    ori_shape = shape_tuple(tensor.shape)
    ori_dtype = dtype_str(tensor.dtype)
    ndim = len(ori_shape)
    assert block_dim < ndim and block_dim >= -ndim

    tensor = flatten_for_quantize(tensor, block_dim)
    # if device.startswith("cuda"):
    #     scales, elements = mxfp_kernels.extract_mxfp_components(
    #         tensor, mxfp_meta=mxfp_meta
    #     )
    # else:
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
    output_dtype: torch.dtype | None = None,
) -> Tensor:
    """
    Compose a tensor from MXFP components.

    :param scales: The shared scales for exponent sharing.
    :type scales: torch.Tensor
    :param elements: The elements of the tensor.
    :type elements: torch.Tensor
    :param tensor_meta: The metadata for the MXFP tensor.
    :type tensor_meta: MXFPTensorMeta
    :param output_dtype: The desired data type of the output tensor, by default None, which uses the dtype from tensor_meta.
    :type dtype: torch.dtype, optional

    :returns: The dequantized tensor.
    :rtype: torch.Tensor
    """
    device = tensor_meta.device
    output_dtype = (
        getattr(torch, tensor_meta.dtype) if output_dtype is None else output_dtype
    )

    # if device.startswith("cuda"):
    #     tensor = mxfp_kernels.compose_mxfp_tensor(
    #         scales=scales,
    #         elements=elements,
    #         mxfp_meta=tensor_meta.meta,
    #         output_dtype=output_dtype,
    #     )
    # else:
    tensor = mxfp_fake.compose_mxfp_tensor(
        scales=scales,
        elements=elements,
        mxfp_meta=tensor_meta.meta,
        output_dtype=output_dtype,
    )

    tensor = permute_for_dequantize(
        tensor, ori_shape=tensor_meta.shape, block_dim=tensor_meta.block_dim
    )
    return tensor



def mxfp_quantizer_sim(
    tensor: Tensor,
    block_dim: int,
    mxfp_meta: MXFPMeta,
    act_tensor: Tensor | None = None,
    dtype: torch.dtype | None = None,
    quantile_search: bool = False,
    cali_batch_size: int = 32,
) -> Tensor:
    out_dq = torch.zeros_like(tensor)
    if quantile_search:
        qtensor = tensor.flatten()
        B = mxfp_meta.block_size

        qtensor = qtensor.reshape(-1, B)  
        # [n_blocks, B], reshape when taking in the whole block for rtn
        # [Hidden, B], for gptq
        best = torch.full([qtensor.shape[0]], float('inf'), device=tensor.device,  dtype=tensor.dtype)
        best_scales, best_elements, tensor_meta = extract_mxfp_components(
            tensor, block_dim, mxfp_meta, percentile=1.0
        )

        percentiles=[1.0, 0.995, 0.99, 0.97, 0.95, 0.93, 0.90, 0.80, 0.70, 0.60, 0.50]
        for percentile in percentiles:
            # this scales is float(), need to fix later
            scales, elements, tensor_meta = extract_mxfp_components(
                tensor, block_dim, mxfp_meta, percentile=percentile
            )
            scale_bias = 2**(mxfp_meta.scale_exp_bits - 1) - 1
            q = elements / 2**(mxfp_meta.element_frac_bits - 1) * 2**(scales - scale_bias)
            # breakpoint()
            q = q.to(dtype=qtensor.dtype)
            # search clipping based on output XW
            if act_tensor != None:
                BATCH_SIZE = cali_batch_size
                # act_tensor is of shape [num_calibrations, sequnce_len, blocksize]
                last_dim = act_tensor.shape[-1]
                if last_dim != B:
                    assert last_dim % B == 0, "Last dimension must be divisible by block size for GPTQ Clip output search"
                    act_tensor = act_tensor.view(*act_tensor.shape[:-1], last_dim // B, B)

                total_batches = act_tensor.shape[0]

                err = torch.zeros(qtensor.shape[0], device=tensor.device, dtype=tensor.dtype)

                with torch.no_grad():
                    for _, b in enumerate(tqdm(range(0, total_batches, BATCH_SIZE), desc="Batching quant output", disable = True)):
                        act_b = act_tensor[b : b + BATCH_SIZE]  # [B, seq_len, hidden]
                        out_q = torch.matmul(act_b, q.T )
                        out_orig = torch.matmul(act_b, qtensor.T)
                        err += torch.norm(out_q - out_orig, p=2, dim=(0, 1))

                        del act_b, out_q, out_orig
                        torch.cuda.empty_cache()

                torch.cuda.empty_cache()
            else:
                # breakpoint()
                q -= qtensor
                q.abs_()
                q.pow_(2)
                err = torch.sum(q, 1)

            tmp = err < best
            if torch.any(tmp):
                # breakpoint()
                best[tmp] = err[tmp]
                best_scales[tmp] = scales[tmp]
                best_elements[tmp] = elements[tmp]

    else:
        scales, elements, tensor_meta = extract_mxfp_components(
            tensor, block_dim, mxfp_meta, percentile=1.0
        )
        best_scales = scales
        best_elements = elements

    out_dq = compose_mxfp_tensor(best_scales, best_elements, tensor_meta, output_dtype=dtype)
    return out_dq





# def mxfp_quantizer_sim(
#     tensor: Tensor,
#     block_dim: int,
#     mxfp_meta: MXFPMeta,
#     output_dtype: torch.dtype | None = None,
#     quantile_search: bool = False,
# ) -> Tensor:
#     """
#     Quantizes and dequantizes a tensor using the MXFP format.

#     :param tensor: The input tensor to be quantized.
#     :type tensor: torch.Tensor
#     :param block_dim: The dimension to group the tensor elements into blocks.
#     :type block_dim: int
#     :param mxfp_meta: The metadata for the MXFP format.
#     :type mxfp_meta: MXFPMeta
#     :param output_dtype: The desired data type of the output tensor, by default None, which uses the dtype from mxfp_meta.

#     :returns: The dequantized tensor.
#     :rtype: torch.Tensor
#     """
#     scales, elements, tensor_meta = extract_mxfp_components(
#         tensor, block_dim, mxfp_meta
#     )
#     tensor_dq = compose_mxfp_tensor(
#         scales, elements, tensor_meta, output_dtype=output_dtype
#     )
#     return tensor_dq
