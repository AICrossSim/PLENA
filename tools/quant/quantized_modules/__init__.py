from .linear import LinearMXFP, LinearMinifloatIEEE
from .embedding import EmbeddingMXFP, EmbeddingMinifloatIEEE
from .rms_norm import RMSNormMinifloatIEEE

QUANTIZED_MODULE_MAP = {
    "linear": {
        "mxfp": LinearMXFP,
        "minifloat_ieee": LinearMinifloatIEEE
    },
    "embedding":{
        "mxfp": EmbeddingMXFP,
        "minifloat_ieee": EmbeddingMinifloatIEEE
    },
    "rms_norm":{
        "minifloat_ieee": RMSNormMinifloatIEEE
    }
}