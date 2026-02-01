"""Flash Attention assembly code generation.

This module has been refactored into the flashattn package.
This file re-exports all functions for backward compatibility.

For new code, prefer importing from compiler.asm_templates.flashattn directly.
"""

# Re-export all functions from the flashattn package for backward compatibility
from .flashattn import (
    qkt_multiply,
    online_softmax_code as _online_softmax_code,
    computing_pv_code as _computing_pv_code,
    computing_o_code as _computing_o_code,
    computing_row_wise_scaling_code as _computing_row_wise_scaling_code,
    reset_fpsram_code as _reset_fpsram_code,
    reset_vssram_code as _reset_vssram_code,
    reset_kv_prefetch as _reset_kv_prefetch,
    flash_attn_asm,
)

# Also export IMM2_BOUND for backward compatibility
IMM2_BOUND = 2**18 - 1

__all__ = [
    "qkt_multiply",
    "_online_softmax_code",
    "_computing_pv_code",
    "_computing_o_code",
    "_computing_row_wise_scaling_code",
    "_reset_fpsram_code",
    "_reset_vssram_code",
    "_reset_kv_prefetch",
    "flash_attn_asm",
    "IMM2_BOUND",
]
