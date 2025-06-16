from .matmul import matmul_mxfp, bmm_mxfp, matmul_minifloat_ieee, matmul_mxint
from .rotary_positional_encoding import apply_rotary_pos_emb_mxfp
from .silu import silu_minifloat_ieee


QUANTIZED_FUNC_MAP = {
    "matmul": {
        "mxfp": matmul_mxfp,
        "minifloat_ieee": matmul_minifloat_ieee,
        "mxint": matmul_mxint
    },
    "bmm": {
        "mxfp": bmm_mxfp,
        "minifloat_ieee": matmul_minifloat_ieee
    },
    "rotary_positional_encoding": {
        "mxfp": apply_rotary_pos_emb_mxfp,
        "minifloat_ieee": matmul_minifloat_ieee
    },
    "silu":{
        "minifloat_ieee": silu_minifloat_ieee
    }

}