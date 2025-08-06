from typing import Literal

import torch
from torch import Tensor

from ..quantizer.mxfp import MXFPMeta
from ..utils import quantize_tensor

def matmul_mxfp(
    input: Tensor,
    other: Tensor,
    input_meta: MXFPMeta | None,
    other_meta: MXFPMeta | None,
    func_type: Literal["XW", "XqW", "XWq", "XqWq"]
) -> Tensor:
    if "Xq" in func_type:
        assert input_meta is not None
        input = quantize_tensor(input, block_dim=-1, meta=input_meta)
    if "Wq" in func_type:
        assert other_meta is not None
        other = quantize_tensor(other, block_dim=-2, meta=other_meta)

    return torch.matmul(input, other)

