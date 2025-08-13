from typing import Literal

import torch
from torch import Tensor

from ..quantizer.mxfp import MXFPMeta
from ..utils import quantize_tensor
from ...rotation.hadamard import OnlineHadamardQuantization

def matmul_mxfp(
    input: Tensor,
    other: Tensor,
    input_meta: MXFPMeta | None,
    other_meta: MXFPMeta | None,
    func_type: Literal["XW", "XqW", "XWq", "XqWq"],
    online_rotate: bool = False
) -> Tensor:
    if "Xq" in func_type:
        assert input_meta is not None
        if online_rotate:
            rotate_quant = OnlineHadamardQuantization(input.shape[-1], block_dim=-1, meta=input_meta)
            input = rotate_quant(input)
        else:
            input = quantize_tensor(input, block_dim=-1, meta=input_meta)

    return torch.matmul(input, other)

