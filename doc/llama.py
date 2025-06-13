import math

import torch
from ..utils import check_shape
from ..utils.int_arith import ceil_div


@torch.no_grad()
def rms_norm(x: torch.Tensor, w: torch.Tensor, s: int, h: int, var_eps: float):
    """
    Args:
        x: (b, s, h), where b = batch size, s = sequence length, h = hidden size
        w: (h,)
        s: sequence length
        h: hidden size
        var_eps: epsilon for variance

    Returns:
        out: (b, s, h)
    """
    b = x.size(0)
    square_bsh = x.pow(2)  # pow = x * x
    sum_bs = square_bsh.sum(dim=2)  # sum over hidden_dim
    var_bs = sum_bs / h  # average over hidden_dim
    sqrt_bs = torch.sqrt(var_bs + var_eps)  # add epsilon to avoid division by zero
    rsqrt_bs = 1.0 / sqrt_bs  # reciprocal of sqrt
    rsqrt_bs1 = rsqrt_bs.unsqueeze(2)  # broadcast to hidden_dim
    x_norm_bsh = x * rsqrt_bs1  # broadcast multiplication
    out_bsh = w * x_norm_bsh  # elementwise scale by weight

    check_shape(x, (b, s, h))
    check_shape(w, (h,))
    check_shape(square_bsh, (b, s, h))
    check_shape(sum_bs, (b, s))
    check_shape(var_bs, (b, s))
    check_shape(sqrt_bs, (b, s))
    check_shape(rsqrt_bs, (b, s))
    check_shape(rsqrt_bs1, (b, s, 1))
    check_shape(x_norm_bsh, (b, s, h))
    check_shape(out_bsh, (b, s, h))
    return out_bsh


@torch.no_grad()
def flash_attn2_head_gemv(q, k, v, qk_scale, s_q, s_kv, h_qkv, Bc, Tc):
    """
    Args:
        q: [b, s_q, h_qkv], query tensor
        k: [b, s_kv, h_qkv], key tensor
        v: [b, s_kv, h_qkv], value tensor
        qk_scale: float, scale factor for qk, usually 1 / sqrt(h_qkv)
        s_q: int, query sequence length, should be 1 for vector-matrix hardware
        s_kv: int, key-value sequence length, increases with generation step (KV cache)
        h_qkv: int, hidden size per head
        Bc: int, tile size for key-value matrix
        Tc: int, temporal tile count

    Returns:
        o: [b, s_q, h_qkv], attention output
    """
    b = q.size(0)

    l = 0.0  # online row sum
    m = float("-inf")  # online row max
    o = torch.zeros(b, s_q, h_qkv, device=q.device)  # output

    for j in range(Tc):
        k_j = k[:, j * Bc : (j + 1) * Bc, :]  # [b, Bc, h_qkv]
        v_j = v[:, j * Bc : (j + 1) * Bc, :]  # [b, Bc, h_qkv]
        s_j = q @ k_j.transpose(1, 2) * qk_scale  # Q @ Kj^T, [b, s_q, Bc]

        rowmax_s_j = s_j.max().cpu().item()  # rowmax(Sj)
        m_new = max(m, rowmax_s_j)  # update global row max
        s_j_shifted = s_j - m_new
        p = torch.exp(s_j_shifted)  # exp(Sj - rowmax(Sj))
        m_res = m - m_new  # m(1) - m(2)
        m = m_new
        l_scale = math.exp(m_res)  # exp(m(1) - m(2))
        p_row_sum = p.sum().cpu().item()
        l = l_scale * l + p_row_sum
        o_scale = math.exp(m_res)
        o = o_scale * o + p @ v_j

    o = 1 / l * o

    assert b == 1, "b must be 1"
    assert s_q == 1, "s_q must be 1"
    check_shape(q, (b, s_q, h_qkv))
    check_shape(k, (b, s_kv, h_qkv))
    check_shape(v, (b, s_kv, h_qkv))
    assert b == 1, "b must be 1"
    assert s_q == 1, "s_q must be 1"
    assert ceil_div(s_kv, Bc) == Tc, f"s_kv={s_kv}, Bc={Bc}, Tc={Tc}"
    check_shape(k_j, (b, 0, h_qkv))  # [1, Bc, h_qkv]
    check_shape(v_j, (b, 0, h_qkv))  # [1, Bc, h_qkv]
    check_shape(s_j, (b, s_q, 0))
    check_shape(o, (b, s_q, h_qkv))
    return o


@torch.no_grad()
def flash_attn2_gemv(
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    qk_scale: float,
    s_q: int,
    s_kv: int,
    h_qkv: int,
    num_q_heads: int,
    num_kv_heads: int,
    Bc: int,
):
    """
    Args:
        q: [b, s_q, num_q_heads, h_qkv], query tensor
        k: [b, s_kv, num_kv_heads, h_qkv], key tensor
        v: [b, s_kv, num_kv_heads, h_qkv], value tensor
        qk_scale: float, scale factor for qk, usually 1 / sqrt(h_qkv)
        s_q: int, query sequence length, should be 1 for vector-matrix hardware
        s_kv: int, key-value sequence length, increases with generation step (KV cache)
        h_qkv: int, hidden size per head
        num_q_heads: int, number of query heads
        num_kv_heads: int, number of key-value heads
        Bc: int, tile size for key-value matrix

    Returns:
        o: [b, s_q, num_q_heads, h_qkv], attention output
    """
    b = q.size(0)  # batch size

    Tc = ceil_div(s_kv, Bc)  # temporal tile count
    num_head_groups = num_q_heads // num_kv_heads

    o = torch.zeros(b, s_q, h_qkv * num_q_heads, device=q.device)  # [b, s_q, h]
    for head_idx in range(num_q_heads):
        q_head = q[:, :, head_idx, :]
        kv_head_idx = head_idx // num_head_groups
        k_head = k[:, :, kv_head_idx, :]
        v_head = v[:, :, kv_head_idx, :]
        o_head = flash_attn2_head_gemv(
            q_head, k_head, v_head, qk_scale=qk_scale, s_q=s_q, s_kv=s_kv, h_qkv=h_qkv, Bc=Bc, Tc=Tc
        )
        o[:, :, head_idx * h_qkv : (head_idx + 1) * h_qkv] = o_head
    o = o.reshape(b, s_q, num_q_heads, h_qkv)

    check_shape(q, (b, s_q, num_q_heads, h_qkv))
    check_shape(k, (b, s_kv, num_kv_heads, h_qkv))
    check_shape(v, (b, s_kv, num_kv_heads, h_qkv))
    check_shape(q_head, (b, s_q, h_qkv))
    check_shape(k_head, (b, s_kv, h_qkv))
    check_shape(v_head, (b, s_kv, h_qkv))
    check_shape(o_head, (b, s_q, h_qkv))

    return o
