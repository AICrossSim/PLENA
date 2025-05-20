from .mxint import mx_int_quantizer
from .minifloat import minifloat_ieee_quantizer
from .mxfp import mxfp_quantizer

__all__ = ["mx_int_quantizer", "minifloat_ieee_quantizer", "mxfp_quantizer"]

QUANTIZER_MAP = {
    "mx_int": mx_int_quantizer,
    "minifloat_ieee": minifloat_ieee_quantizer,
    "mxfp": mxfp_quantizer
}