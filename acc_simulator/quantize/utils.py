from torch import Tensor
import warnings

from .quantizer.mxfp import MXFPMeta, mxfp_quantizer_sim
from .quantizer.mxint import MXIntMeta, mxint_quantizer_sim
from .quantizer.minifloat import MinifloatMeta, minifloat_quantizer_sim


def quantize_tensor(input: Tensor, block_dim: int, meta: MXFPMeta | MXIntMeta, quantile_search: bool = False):
    if isinstance(meta, MXFPMeta):
        return mxfp_quantizer_sim(input, block_dim=block_dim, mxfp_meta=meta, quantile_search=quantile_search)
    elif isinstance(meta, MXIntMeta):
        return mxint_quantizer_sim(input, block_dim=block_dim, mxint_meta=meta, quantile_search=quantile_search)
    elif isinstance(meta, MinifloatMeta):
        return minifloat_quantizer_sim(input, block_dim=block_dim, minifloat_meta=meta)
    else:
        print(f"[DEBUG] Invalid meta: {meta}, returning input as is")
        return input