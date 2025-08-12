from typing import Literal

from torch import Tensor

from ..quantizer.mxfp import MXFPMeta
from ..quantizer.mxint import MXIntMeta
from ..utils import quantize_tensor
from ...rotation.hadamard import OnlineHadamardQuantization


def kv_cache_mxfp(
    key_states: Tensor,
    value_states: Tensor,
    kv_cache_meta: MXFPMeta | MXIntMeta | None,
    func_type: Literal["KV", "KVq"],
    online_rotate: bool = False
) -> tuple[Tensor, Tensor]:
    if func_type == "KVq":
        assert kv_cache_meta is not None
        if online_rotate:
            rotate_quant = OnlineHadamardQuantization(key_states.shape[-1], block_dim=-1, meta=kv_cache_meta)
            key_states = rotate_quant(key_states)
            value_states = rotate_quant(value_states)
        else:
            key_states_q = quantize_tensor(key_states, block_dim=-1, meta=kv_cache_meta, quantile_search=False)
            value_states_q = quantize_tensor(value_states, block_dim=-1, meta=kv_cache_meta, quantile_search=False)
        return key_states_q, value_states_q
    else:
        return key_states, value_states
