from typing import Literal, Optional, Tuple, Any
import torch
from torch import Tensor, nn, LongTensor
from transformers.models.llama.modeling_llama import (
    Cache,
    LlamaAttention,
    repeat_kv,
)

# Handle optional imports for newer transformers versions
_HAS_FLASH_ATTENTION_KWARGS = False
try:
    from transformers.models.llama.modeling_llama import FlashAttentionKwargs
    from typing import Unpack
    _HAS_FLASH_ATTENTION_KWARGS = True
except ImportError:
    pass

from ...quantize.quantizer.mxfp import MXFPMeta
from ...quantize.quantized_functions import matmul_mxfp, rope_minifloat, softmax_minifloat, kv_cache_mxfp
from ...quantize.quantizer.minifloat import MinifloatMeta


class LlamaAttentionMXFP(LlamaAttention):
    def __init__(
        self,
        config,
        layer_idx,
        qk_q_meta: MXFPMeta | None,
        qk_k_meta: MXFPMeta | None,
        qk_func_type: Literal["XW", "XqW", "XWq", "XqWq"] | None,
        av_a_meta: MXFPMeta | None,
        av_v_meta: MXFPMeta | None,
        av_func_type: Literal["XW", "XqW", "XWq", "XqWq"] | None,
        rope_meta: MinifloatMeta | None,
        rope_func_type: Literal["X", "Xq"] | None,
        softmax_meta: MinifloatMeta | None,
        softmax_func_type: Literal["X", "Xq"] | None,
        kv_cache_meta: MXFPMeta | None,
        kv_func_type: Literal["KV", "KVq"] | None,
        online_rotate: bool
    ):
        super().__init__(config, layer_idx)
        self.config = config
        self.qk_q_meta = qk_q_meta
        self.qk_k_meta = qk_k_meta
        self.qk_func_type = qk_func_type
        self.av_a_meta = av_a_meta
        self.av_v_meta = av_v_meta
        self.av_func_type = av_func_type
        self.rope_meta = rope_meta
        self.rope_func_type = rope_func_type
        self.softmax_meta = softmax_meta
        self.softmax_func_type = softmax_func_type
        self.kv_cache_meta = kv_cache_meta
        self.kv_func_type = kv_func_type
        self.online_rotate = online_rotate

    def forward(
        self,
        hidden_states: Tensor,
        position_embeddings: Tuple[Tensor, Tensor],
        attention_mask: Optional[Tensor],
        past_key_value: Optional[Cache] = None,
        cache_position: Optional[LongTensor] = None,
        **kwargs,
    ) -> Tuple[Tensor, Optional[Tensor], Optional[Tuple[Tensor]]]:
        # [batch_size, seq_length]
        input_shape = hidden_states.shape[:-1]
        # [batch_size, seq_length, num_heads, head_dim]
        # -1 infers num_heads = hidden_dim // head_dim
        hidden_shape = (*input_shape, -1, self.head_dim)

        # hidden_states.shape == [batch_size, seq_length, hidden_dim]
        # [batch_size, num_heads, seq_length, head_dim]
        query_states = self.q_proj(hidden_states).view(hidden_shape).transpose(1, 2)
        key_states = self.k_proj(hidden_states).view(hidden_shape).transpose(1, 2)
        value_states = self.v_proj(hidden_states).view(hidden_shape).transpose(1, 2)

        cos, sin = position_embeddings 
        # query_states, key_states = apply_rotary_pos_emb(
        #     query_states, key_states, cos, sin
        # )
        query_states, key_states = rope_minifloat(query_states, 
                                                  key_states, 
                                                  cos, 
                                                  sin, 
                                                  self.rope_meta, 
                                                  self.rope_func_type)

        if past_key_value is not None:
            # sin and cos are specific to RoPE models; cache_position needed for the static cache
            cache_kwargs = {"sin": sin, "cos": cos, "cache_position": cache_position}

            key_states, value_states = kv_cache_mxfp(key_states, 
                                                       value_states, 
                                                       self.kv_cache_meta, 
                                                       self.kv_func_type,
                                                       self.online_rotate)

            key_states, value_states = past_key_value.update(
                key_states, value_states, self.layer_idx, cache_kwargs
            )

        attention_interface: callable = eager_attention_forward_mxfp

        attn_output, attn_weights = attention_interface(
            self,
            query_states,
            key_states,
            value_states,
            attention_mask,
            dropout=0.0 if not self.training else self.attention_dropout,
            scaling=self.scaling,
            qk_q_meta=self.qk_q_meta,
            qk_k_meta=self.qk_k_meta,
            qk_func_type=self.qk_func_type,
            av_a_meta=self.av_a_meta,
            av_v_meta=self.av_v_meta,
            av_func_type=self.av_func_type,
            softmax_meta=self.softmax_meta,
            softmax_func_type=self.softmax_func_type,
            online_rotate=self.online_rotate,
            **kwargs,
        )

        # (batch_size, seq_len, num_heads, head_dim) → (batch_size, seq_len, num_heads * head_dim)
        attn_output = attn_output.reshape(*input_shape, -1).contiguous()

        attn_output = self.o_proj(attn_output)
        return attn_output, attn_weights

    @classmethod
    def from_attention(
        cls,
        attention: LlamaAttention,
        qk_q_meta: MXFPMeta | None,
        qk_k_meta: MXFPMeta | None,
        qk_func_type: Literal["XW", "XqW", "XWq", "XqWq"] | None,
        av_a_meta: MXFPMeta | None,
        av_v_meta: MXFPMeta | None,
        av_func_type: Literal["XW", "XqW", "XWq", "XqWq"] | None,
        rope_meta: MinifloatMeta | None,
        rope_func_type: Literal["X", "Xq"] | None,
        softmax_meta: MinifloatMeta | None,
        softmax_func_type: Literal["X", "Xq"] | None,
        kv_cache_meta: MXFPMeta | None,
        kv_func_type: Literal["KV", "KVq"] | None,
        online_rotate: bool
    ):
        new_attn = cls(
            config=attention.config,
            layer_idx=attention.layer_idx,
            qk_q_meta=qk_q_meta,
            qk_k_meta=qk_k_meta,
            qk_func_type=qk_func_type,
            av_a_meta=av_a_meta,
            av_v_meta=av_v_meta,
            av_func_type=av_func_type,
            rope_meta=rope_meta,
            rope_func_type=rope_func_type,
            softmax_meta=softmax_meta,
            softmax_func_type=softmax_func_type,
            kv_cache_meta=kv_cache_meta,
            kv_func_type=kv_func_type,
            online_rotate=online_rotate
        )
        device, dtype = next(attention.parameters()).device, next(attention.parameters()).dtype
        new_attn = new_attn.to(dtype=dtype, device=device)
        # load q/k/v/o projections
        # this assumes that the projections are not quantized yet
        new_attn.load_state_dict(attention.state_dict(), strict=True)
        return new_attn


def eager_attention_forward_mxfp(
    module: nn.Module,
    query: Tensor,
    key: Tensor,
    value: Tensor,
    attention_mask: Optional[Tensor],
    scaling: float,
    dropout: float = 0.0,
    qk_q_meta: MXFPMeta | None = None,
    qk_k_meta: MXFPMeta | None = None,
    qk_func_type: Literal["XW", "XqW", "XWq", "XqWq"] | None = None,
    av_a_meta: MXFPMeta | None = None,
    av_v_meta: MXFPMeta | None = None,
    softmax_meta: MinifloatMeta | None = None,
    softmax_func_type: Literal["X", "Xq"] | None = None,
    av_func_type: Literal["XW", "XqW", "XWq", "XqWq"] | None = None,
    online_rotate: bool = False,
    **kwargs,
):
    key_states = repeat_kv(key, module.num_key_value_groups)
    value_states = repeat_kv(value, module.num_key_value_groups)

    # attn_weights = torch.matmul(query, key_states.transpose(2, 3)) * scaling
    # *: quantized QK matmul if meta is not None
    attn_weights = matmul_mxfp(
        query,
        key_states.transpose(2, 3),
        input_meta=qk_q_meta,
        other_meta=qk_k_meta,
        func_type=qk_func_type,
        online_rotate=online_rotate
    )
    attn_weights = attn_weights * scaling


    if attention_mask is not None:
        causal_mask = attention_mask[:, :, :, : key_states.shape[-2]]
        attn_weights = attn_weights + causal_mask

    attn_weights = softmax_minifloat(
        attn_weights, 
        softmax_meta, 
        softmax_func_type, 
        dim=-1
    )
    
    attn_weights = nn.functional.dropout(
        attn_weights, p=dropout, training=module.training
    )
    # *: quantized AV matmul if meta is not None
    attn_output = matmul_mxfp(
        attn_weights,
        value_states,
        input_meta=av_a_meta,
        other_meta=av_v_meta,
        func_type=av_func_type,
        online_rotate=online_rotate
    )
    # attn_output = torch.matmul(attn_weights, value_states)
    attn_output = attn_output.transpose(1, 2).contiguous()

    return attn_output, attn_weights
