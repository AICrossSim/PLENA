from typing import Literal

import torch
from torch import Tensor

from mase_triton.mxfp.functional import quantize_dequantize as mxfp_quantizer_sim
from ..quantizer.mxfp import MXFPMeta


def matmul_mxfp(
    input: Tensor,
    other: Tensor,
    input_meta: MXFPMeta | None,
    other_meta: MXFPMeta | None,
    func_type: Literal["XW", "XqW", "XWq", "XqWq"]
) -> Tensor:
    if "Xq" in func_type:
        assert input_meta is not None
        input = mxfp_quantizer_sim(input, block_dim=-1, mxfp_meta=input_meta)
    if "Wq" in func_type:
        assert other_meta is not None
        other = mxfp_quantizer_sim(input, block_dim=-2, mxfp_meta=input_meta)

    return torch.matmul(input, other)

