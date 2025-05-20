from functools import partial

import torch

from ..quantizer import mxfp_quantizer

def rotate_half(x):
    """Rotates half the hidden dims of the input."""
    x1 = x[..., : x.shape[-1] // 2]
    x2 = x[..., x.shape[-1] // 2 :]
    return torch.cat((-x2, x1), dim=-1)


def apply_rotary_pos_emb_mxfp(q, k, cos, sin, quant_config, position_ids=None, unsqueeze_dim=1):
    """Applies Rotary Position Embedding to the query and key tensors.

    Args:
        q (`torch.Tensor`): The query tensor.
        k (`torch.Tensor`): The key tensor.
        cos (`torch.Tensor`): The cosine part of the rotary embedding.
        sin (`torch.Tensor`): The sine part of the rotary embedding.
        position_ids (`torch.Tensor`, *optional*):
            Deprecated and unused.
        unsqueeze_dim (`int`, *optional*, defaults to 1):
            The 'unsqueeze_dim' argument specifies the dimension along which to unsqueeze cos[position_ids] and
            sin[position_ids] so that they can be properly broadcasted to the dimensions of q and k. For example, note
            that cos[position_ids] and sin[position_ids] have the shape [batch_size, seq_len, head_dim]. Then, if q and
            k have the shape [batch_size, heads, seq_len, head_dim], then setting unsqueeze_dim=1 makes
            cos[position_ids] and sin[position_ids] broadcastable to the shapes of q and k. Similarly, if q and k have
            the shape [batch_size, seq_len, heads, head_dim], then set unsqueeze_dim=2.
    Returns:
        `tuple(torch.Tensor)` comprising of the query and key tensors rotated using the Rotary Position Embedding.
    """
    if quant_config.get("bypass", False):
        freq_quantizer = lambda x: x
    else:
        freq_quantizer = partial(
            mxfp_quantizer,
            width=quant_config["data_in_width"],
            exponent_width=quant_config["data_in_exponent_width"],
            exponent_bias_width=quant_config["data_in_exponent_bias_width"],
            block_size=quant_config["data_in_block_size"],
            skip_first_dim=False,
        )

    # Unsqueeze cos/sin to make them broadcastable to q/k
    cos = freq_quantizer(cos.unsqueeze(unsqueeze_dim))
    sin = freq_quantizer(sin.unsqueeze(unsqueeze_dim))

    # Apply rotary embedding and Quantize the output again
    q_embed = freq_quantizer((q * cos) + (rotate_half(q) * sin))
    k_embed = freq_quantizer((k * cos) + (rotate_half(k) * sin))

    return q_embed, k_embed
