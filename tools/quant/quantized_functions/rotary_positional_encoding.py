from functools import partial

import torch

from ..quantizer import mxfp_quantizer

def rotate_half(x):
    """Rotates half the hidden dims of the input."""
    x1 = x[..., : x.shape[-1] // 2]
    x2 = x[..., x.shape[-1] // 2 :]
    return torch.cat((-x2, x1), dim=-1)


def apply_rotary_pos_emb_mxfp(q, k, cos, sin, quant_config, position_ids=None, unsqueeze_dim=1):
    """Applies Rotary Position Embedding to the query and key tensors."""
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

    cos = freq_quantizer(cos)
    sin = freq_quantizer(sin)
    
    # Reshape cos and sin to match q's dimensions
    cos = cos.unsqueeze(unsqueeze_dim)
    sin = sin.unsqueeze(unsqueeze_dim)
    
    # Ensure cos/sin have the same sequence length as q/k
    seq_len = q.size(-2)
    cos = cos[..., :seq_len, :]
    sin = sin[..., :seq_len, :]

    # Apply RoPE with quantized sin/cos
    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)

    return q_embed, k_embed