from .matmul import matmul_mxfp, bmm_mxfp, matmul_minifloat_ieee
from .rotary_positional_encoding import apply_rotary_pos_emb_mxfp, apply_rotary_pos_emb_minifloat_ieee
from .silu import silu_minifloat_ieee
from .softmax import softmax_minifloat_ieee


QUANTIZED_FUNC_MAP = {
    "matmul": {
        "mxfp": matmul_mxfp,
        "minifloat_ieee": matmul_minifloat_ieee
    },
    "bmm": {
        "mxfp": bmm_mxfp,
        "minifloat_ieee": matmul_minifloat_ieee
    },
    "rotary_positional_encoding": {
        "mxfp": apply_rotary_pos_emb_mxfp,
        "minifloat_ieee": apply_rotary_pos_emb_minifloat_ieee
    },
    "silu":{
        "minifloat_ieee": silu_minifloat_ieee
    },
    "softmax":{
        "minifloat_ieee": softmax_minifloat_ieee
    }
}