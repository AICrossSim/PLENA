from torch import Tensor

from .quantizer.mxfp import MXFPMeta, mxfp_quantizer_sim
from .quantizer.mxint import MXIntMeta, mxint_quantizer_sim
from .quantizer.minifloat import MinifloatMeta, minifloat_quantizer_sim


def quantize_tensor(input: Tensor, block_dim: int, meta: MXFPMeta | MXIntMeta):
    if isinstance(meta, MXFPMeta):
        return mxfp_quantizer_sim(input, block_dim=block_dim, mxfp_meta=meta)
    elif isinstance(meta, MXIntMeta):
        return mxint_quantizer_sim(input, block_dim=block_dim, mxint_meta=meta)
    elif isinstance(meta, MinifloatMeta):
        return minifloat_quantizer_sim(input, block_dim=block_dim, minifloat_meta=meta)
    else:
        raise ValueError(f"Invalid meta: {meta}")