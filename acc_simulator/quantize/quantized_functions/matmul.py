from typing import Literal

import torch
from torch import Tensor

from ..quantizer.mxfp import MXFPMeta, mxfp_quantizer_sim
from ..quantizer.minifloat import MinifloatMeta, minifloat_ieee_quantizer

def matmul_mxfp(
    input: Tensor,
    other: Tensor,
    input_meta: MXFPMeta | None,
    other_meta: MXFPMeta | None,
    output_meta: MinifloatMeta | None,
    func_type: Literal["XW", "XqW", "XWq", "XqWq"]
) -> Tensor:
    if "Xq" in func_type:
        assert input_meta is not None
        input = mxfp_quantizer_sim(input, block_dim=-1, mxfp_meta=input_meta)
    if "Wq" in func_type:
        assert other_meta is not None
        other = mxfp_quantizer_sim(input, block_dim=-2, mxfp_meta=input_meta)

    output = torch.matmul(input, other)
    if output_meta is not None:
        output = minifloat_ieee_quantizer(output, meta=output_meta)

    return output

