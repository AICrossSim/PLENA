from .matmul import matmul_mxfp, bmm_mxfp
from .rotary_positional_encoding import apply_rotary_pos_emb_mxfp

QUANTIZED_FUNC_MAP = {
    "matmul": {
        "mxfp": matmul_mxfp
    },
    "bmm": {
        "mxfp": bmm_mxfp
    },
    "rotary_positional_encoding": {
        "mxfp": apply_rotary_pos_emb_mxfp
    },
}