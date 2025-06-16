from .linear import LinearMXFP, LinearMinifloatIEEE, LinearMXINT
from .embedding import EmbeddingMXFP
from .rms_norm import RMSNormMINIFP

QUANTIZED_MODULE_MAP = {
    "linear": {
        "mxfp": LinearMXFP,
        "minifloat_ieee": LinearMinifloatIEEE,
        "mxint": LinearMXINT
    },
    "embedding":{
        "mxfp": EmbeddingMXFP,
    },
    "rms_norm":{
        "minifloat_ieee": RMSNormMINIFP
    }
}