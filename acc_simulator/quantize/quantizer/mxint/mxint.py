import torch
from torch import Tensor
from torch.nn import functional as F
from tqdm import tqdm

from .meta import MXIntMeta, MXIntTensorMeta
from .fake import extract_mxint_components as extract_mxint_components_fake, compose_mxint_tensor as compose_mxint_tensor_fake
from ..mxfp.helpers import flatten_for_quantize, permute_for_dequantize



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
    act_tensor: Tensor | None = None,
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
    tensor.to(torch.float16)

    out_dq = torch.zeros_like(tensor)
    # tensor
    if quantile_search:
        # breakpoint()
        qtensor = tensor.flatten()
        B = mxint_meta.block_size

        qtensor = qtensor.reshape(-1, B)  # [n_blocks, B]

        # qtensor should be hidden, B instead of n_blocks，when rtn call, it is different
        best = torch.full([qtensor.shape[0]], float('inf'), device=tensor.device,  dtype=tensor.dtype)
        best_scales, best_elements, tensor_meta = extract_mxint_components(
            tensor, block_dim, mxint_meta, percentile=1.0
        )
        # percentiles = [
        #     1.0,
        #     0.999, 0.998, 0.997, 0.995, 0.99,
        #     0.98, 0.97, 0.96, 0.95,
        #     0.93,
        #     0.87, 0.85, 0.83,
        #     0.75, 0.65, 0.55,
        # ]
        # shorter version of p
        percentiles=[1.0, 0.99, 0.97, 0.95, 0.90, 0.80, 0.70, 0.60, 0.50]
        for percentile in percentiles:
            # this scales is float(), need to fix later
            scales, elements, tensor_meta = extract_mxint_components(
                tensor, block_dim, mxint_meta, percentile=percentile
            )
            scale_bias = 2**(mxint_meta.scale_bits - 1) - 1
            # similarity = _get_similarity(tensor, tensor_dq, metric="l2norm").mean().abs()
            q = elements / 2**(mxint_meta.element_bits - 1) * 2**(scales - scale_bias)
            # the blocked weghts after quantization, q is of shape [hiddensize, block_size]
            # act_tensor is of shape [128, sequnce_len, blocksize]

            q =q.to(torch.float16)
            
            hidden_dim = q.T.shape[-1]
            # if hidden_dim> 4096:
            #     BATCH_SIZE = 32
            # else:
                # BATCH_SIZE = 128
            # breakpoint()
            # TODO: temp batch_size for looping over the calibration activations
            BATCH_SIZE = 16
            # search clipping based on output XW
            if act_tensor != None:
                act_tensor = act_tensor.to(torch.float16)

                last_dim = act_tensor.shape[-1]
                if last_dim != B:
                    assert last_dim % B == 0, "Last dimension must be divisible by block size"
                    act_tensor = act_tensor.view(*act_tensor.shape[:-1], last_dim // B, B)

                total_batches = act_tensor.shape[0]

                out_after_quant_list = []
                out_before_quant_list = []
                # breakpoint()
                with torch.no_grad():
                    for _, b in enumerate(tqdm(range(0, total_batches, BATCH_SIZE), desc="Batching quant output", disable = True)):
                        act_b = act_tensor[b : b + BATCH_SIZE]  # [B, seq_len, hidden]
    
                        out_q = torch.matmul(act_b, q.T )
                        out_orig = torch.matmul(act_b, qtensor.T)

                        out_after_quant_list.append(out_q)
                        out_before_quant_list.append(out_orig)

                        # Free up memory
                        del act_b, out_q, out_orig, q_dev, qtensor_dev
                        torch.cuda.empty_cache()

                # Combine all outputs
                out_after_quant = torch.cat(out_after_quant_list, dim=0)
                out_before_quant = torch.cat(out_before_quant_list, dim=0)
                
                use_snr = False
                if use_snr:
                    signal_power = torch.norm(out_before_quant, p=2, dim=(0, 1)) ** 2
                    noise_power = torch.norm(out_before_quant - out_after_quant, p=2, dim=(0, 1)) ** 2
                    snr = 10 * torch.log10(signal_power / (noise_power + 1e-8))
                    err = -snr  # Lower SNR = higher error
                else:
                    diff = (out_after_quant - out_before_quant)
                    l2_per_channel = torch.norm(diff, p=2, dim=(0, 1))  # shape [out_features]
                    err = l2_per_channel
                del out_after_quant, out_before_quant
                torch.cuda.empty_cache()
            else:
                q -= qtensor
                q.abs_()
                q.pow_(2)
                err = torch.sum(q, 1)

            tmp = err < best
            if torch.any(tmp):
                best[tmp] = err[tmp]
                best_scales[tmp] = scales[tmp]
                best_elements[tmp] = elements[tmp]

    else:
        scales, elements, tensor_meta = extract_mxint_components(
            tensor, block_dim, mxint_meta, percentile=1.0
        )
        best_scales = scales
        best_elements = elements
    
    out_dq = compose_mxint_tensor(best_scales, best_elements, tensor_meta, dtype=dtype)
    return out_dq


