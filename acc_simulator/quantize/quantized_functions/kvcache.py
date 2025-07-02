from typing import Literal

from torch import Tensor

from ..quantizer.mxfp import MXFPMeta, mxfp_quantizer_sim


def kv_cache_mxfp(
    key_states: Tensor,
    value_states: Tensor,
    kv_cache_meta: MXFPMeta | None,
    func_type: Literal["KV", "KVq"]
) -> tuple[Tensor, Tensor]:
    if func_type == "KVq":
        assert kv_cache_meta is not None
        key_states_q = mxfp_quantizer_sim(key_states, block_dim=-1, mxfp_meta=kv_cache_meta)
        value_states_q = mxfp_quantizer_sim(value_states, block_dim=-1, mxfp_meta=kv_cache_meta)
        return key_states_q, value_states_q
    else:
        return key_states, value_states
