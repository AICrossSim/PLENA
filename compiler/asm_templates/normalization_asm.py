from code_gen_op import _generate_vector_op
def rms_norm_asm(
    # qk hbm addresses
    q_hbm_address: int,
    _n_offset: int,
    _eps_offset: int,
    # qkv sram addresses
    q_base_address: int,
    k_base_address: int,
    v_base_address: int,
    # model info
    mlen: int,
    vlen: int,
    head_dim: int,
    hidden_dim: int,
    blen: int 
) -> str:
    """
    Generate assembly code for L2 normalization.
    """

    _n_offset = "TODO"
    _eps_offset = "TODO"
        
    square_code = _generate_vector_op(
        {
            "name": "VMultVv",
            "type": "vector",
            "reg_in_0": "i0",
            "reg_in_1": "i0",
            "reg_out": "i1",
            "loops": hidden_dim // vlen
        })
    reduction_code = _generate_vector_op(
        {
            "name": "VRedSum",
            "type": "vector",
            "reg_in_0": "i1",
            "reg_out": "f0",
            "loops": hidden_dim // vlen
        })
    generated_code = f"""
    ; RMS Normalization: hidden_dim={hidden_dim},
    ; Compute RMS and normalize
    ; initialize reg
    LDI i0, 0
    SAddiInt i0, i0, 0
    SAddiInt i1, i0, 0
    ; compute square x^2
    {square_code}

    ; compute reduction sum, output to f0
    {reduction_code}

    ; compute load 1/n to f1
    SAddiInt i3, i0, {_n_offset}
    SLdFp f1, i3, 0

    ; compute variance
    SMulInt f0, f0, f1

    ; eps + variance
    SAddiInt i3, i0, {_eps_offset}
    SLdFp f1, i3, 0
    SAddFp f0, f0, f1

    ; compute RMS
    SSqrtFp f0, f0
    SReciFp f0, f0

    ; load 1/n to f1
    SAddiInt i3, i0, {_n_offset}
    SLdFp f1, i3, 0

    ; normalize

    ; store result
    """

    return f"""

"""