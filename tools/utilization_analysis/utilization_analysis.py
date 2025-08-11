import os
from typing import Dict, List, Any, Optional

def _report_flash_attn_utilization(node: Dict[str, Any], model_info: Dict[str, Any], mode: str, input_seq_len: int, M: int, N: int, K: int) -> None:
    """
    Report the utilization of flash attention for a given node.
    """
    dims = node["dimensions"]
    batch_size = model_info.get("batch", 1),
    hidden_size = dims["hidden_size"]
    num_attn_heads = dims["num_attention_heads"]
    num_kv_heads = dims["num_kv_heads"]

    head_dim = dims["head_dim"]
    input_token_size = input_seq_len
    theoretical_operation = 0
    attainable_operation = 0
    
    if mode == "prefilling":
        # Projection
        operation_amount = (hidden_size // M) * ((head_dim * num_attn_heads) // K) * (input_token_size // N) * batch_size + (hidden_size // M) * ((head_dim * num_kv_heads) // K) * (input_token_size // N) * batch_size
        attainable_operation    += operation_amount * (M * K)
        theoretical_operation   += operation_amount * (M * K)

        # QKT
        operation_amount = num_attn_heads * (head_dim // K) * (input_token_size // N) * (input_token_size // N) * batch_size
        attainable_operation    += operation_amount * (M * K)
        if K > head_dim:
            operation_amount *= (K // head_dim)
        
        theoretical_operation   += operation_amount * (M * K)
    
    else:
        # Decoding
        # Projection
        operation_amount = (hidden_size // M) * ((head_dim * num_attn_heads) // K) * batch_size + (hidden_size // M) * ((head_dim * num_kv_heads) // K) * batch_size
        attainable_operation    += operation_amount * (batch_size * K)
        theoretical_operation   += operation_amount * (M * K)

        # QKT
        operation_amount = num_attn_heads * (head_dim // K) * batch_size * batch_size
        attainable_operation    += operation_amount * (M * K)
        if K > head_dim:
            operation_amount *= (K // head_dim)

        theoretical_operation   += operation_amount * (M * K)
