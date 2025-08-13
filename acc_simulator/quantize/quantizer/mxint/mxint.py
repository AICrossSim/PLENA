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
    tensor = flatten_for_quantize(tensor, block_dim)
    
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
    dtype = getattr(torch, tensor_meta.dtype) if dtype is None else dtype

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
    quantile_search: bool = False,
    cali_batch_size: int = 32,
) -> Tensor:
    out_dq = torch.zeros_like(tensor)
    if quantile_search:
        qtensor = tensor.flatten()
        B = mxint_meta.block_size

        qtensor = qtensor.reshape(-1, B)  

        percentiles=torch.tensor([1.0, 0.999, 0.995, 0.99, 0.97, 0.95, 0.93, 0.90, 0.80, 0.70, 0.60], device=tensor.device, dtype=torch.float32)

        device = str(tensor.device)
        ori_shape = tuple(tensor.shape)
        ori_dtype = str(tensor.dtype).removeprefix("torch.")
        ndim = len(ori_shape)
        assert block_dim < ndim and block_dim >= -ndim
        tensor = flatten_for_quantize(tensor, block_dim)

        # assert x.numel() % B == 0, (
        #     f"Input tensor size {x.numel()} is not divisible by block size {B}."
        # )
        x = tensor
        B = mxint_meta.block_size
        n_blocks = x.numel() // B

        x = x.flatten()
        x = x.reshape(n_blocks, B)  # [n_blocks, B]

        ori_dtype = x.dtype
        # quantile need fp32
        x_max = x.abs().to(torch.float32).quantile(percentiles, dim=1, keepdim=True).to(ori_dtype)

        scale = x_max.log2().ceil()
        scale_bias = 2**(mxint_meta.scale_bits - 1) - 1
        x = x / 2**scale
        x_mant = x * 2**(mxint_meta.element_bits - 1)
        scale = scale + scale_bias
        scale = scale.clamp(min=0, max=2**mxint_meta.scale_bits-1)
        x_mant = x_mant.round().clamp(min=-2**(mxint_meta.element_bits-1), max=2**(mxint_meta.element_bits-1)-1)

        quant_tensor = x_mant / 2**(mxint_meta.element_bits - 1) * 2**(scale - scale_bias)
        quant_tensor = quant_tensor.reshape(len(percentiles), n_blocks, B)
        if act_tensor is None:
            err = torch.norm(quant_tensor - qtensor, p=2, dim=-1)
            min_err_idx = torch.argmin(err, dim=0).reshape(-1)
        else:
            last_dim = act_tensor.shape[-1]
            if last_dim != B:
                assert last_dim % B == 0, "Last dimension must be divisible by block size for GPTQ Clip output search"
                act_tensor = act_tensor.view(*act_tensor.shape[:-1], last_dim // B, B)
            
            out_orig = torch.matmul(act_tensor, qtensor.T)
            out_q = torch.matmul(act_tensor, quant_tensor.T)
            err = torch.norm(out_q - out_orig, p=2, dim=(1, 2))
            min_err_idx = torch.argmin(err, dim=0)

        best_scales = scale[min_err_idx, torch.arange(scale.shape[1])]
        best_elements = x_mant[min_err_idx, torch.arange(x_mant.shape[1])]

        tensor_meta = MXIntTensorMeta(
            device=device,
            dtype=ori_dtype,
            shape=ori_shape,
            block_dim=block_dim,
            meta=mxint_meta,
        )

        # q = q.reshape(n_blocks, B)
        # q -= qtensor



        # for percentile in percentiles:
        #     # this scales is float(), need to fix later
        #     scales, elements, tensor_meta = extract_mxint_components(
        #         tensor, block_dim, mxint_meta, percentile=percentile
        #     )
        #     scale_bias = 2**(mxint_meta.scale_bits - 1) - 1
        #     q = elements / 2**(mxint_meta.element_bits - 1) * 2**(scales - scale_bias)

        #     # search clipping based on output XW 
        #     if act_tensor != None:
        #         # BATCH_SIZE = cali_batch_size
        #         # act_tensor is of shape [num_calibrations, sequnce_len, blocksize]
        #         out_orig = torch.matmul(act_tensor, qtensor.T)
        #         last_dim = act_tensor.shape[-1]
        #         if last_dim != B:
        #             assert last_dim % B == 0, "Last dimension must be divisible by block size for GPTQ Clip output search"
        #             act_tensor = act_tensor.view(*act_tensor.shape[:-1], last_dim // B, B)


        #         # total_batches = act_tensor.shape[0]


        #         with torch.no_grad():
        #             out_q = torch.matmul(act_tensor, q.T)
        #             err = torch.norm(out_q - out_orig, p=2, dim=(0, 1))
        #             del out_q
        #             # torch.cuda.empty_cache()

        #             # breakpoint()
        #             # for _, b in enumerate(tqdm(range(0, total_batches, BATCH_SIZE), desc="Batching quant output", disable = True)):
        #             #     act_b = act_tensor[b : b + BATCH_SIZE]  # [B, seq_len, hidden]
        #             #     out_q = torch.matmul(act_b, q.T )
        #             #     out_orig = torch.matmul(act_b, qtensor.T)
        #             #     err += torch.norm(out_q - out_orig, p=2, dim=(0, 1))

        #             #     del act_b, out_q, out_orig
        #             #     torch.cuda.empty_cache()

        #         torch.cuda.empty_cache()
        #     else:
        #         q -= qtensor
        #         q.abs_()
        #         q.pow_(2)
        #         err = torch.sum(q, 1)

        #     breakpoint()
        #     tmp = err < best
        #     if torch.any(tmp):
        #         best[tmp] = err[tmp]
        #         best_scales[tmp] = scales[tmp]
        #         best_elements[tmp] = elements[tmp]

    else:
        scales, elements, tensor_meta = extract_mxint_components(
            tensor, block_dim, mxint_meta, percentile=1.0
        )
        best_scales = scales
        best_elements = elements
    
    out_dq = compose_mxint_tensor(best_scales, best_elements, tensor_meta, dtype=dtype)
    return out_dq


