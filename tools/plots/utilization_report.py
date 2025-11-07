import os
from typing import Dict, List, Any, Optional

def _report_flash_attn_utilization( model_info: Dict[str, Any], mode: str, input_token_len: int, M: int, N: int, K: int) -> None:
    """
    Report the utilization of flash attention for a given node.
    """
    batch_size = model_info["batch_size"]
    hidden_size = 8192
    num_attn_heads = 64
    num_kv_heads = 8
    head_dim = 128
    context_len = model_info.get("context_len", 5000)
    input_token_size = context_len
    theoretical_operation = 0
    attainable_operation = 0
    overall_operation_amount = 0
    
    if mode == "prefilling":
        # Prefilling
        # Projection
        operation_amount = ((head_dim * num_attn_heads)  // M) * ( hidden_size // K) * (input_token_len // N) + ((head_dim * num_kv_heads) // M) * ( hidden_size // K) * (input_token_len // N) * 2
        overall_operation_amount    += operation_amount
        attainable_operation        += operation_amount * (M * K * N)
        theoretical_operation       += operation_amount * (M * K * N)

        # QKT
        operation_amount =  batch_size * num_attn_heads * (head_dim // K) * (input_token_size // M) * (input_token_len // N)
        overall_operation_amount    += operation_amount
        attainable_operation        += operation_amount * (M * K * N)
        theoretical_operation       += operation_amount * (M * K * N)

        # PV
        operation_amount =  batch_size * num_attn_heads * (input_token_size // K) * (head_dim // N) * (head_dim // M)
        overall_operation_amount    += operation_amount
        attainable_operation        += operation_amount * (M * K * N)
        theoretical_operation       += operation_amount * (M * K * N)

    else:
        # Decoding input token len is 
        # Projection
        operation_amount = ((head_dim * num_attn_heads)  // M) * ( hidden_size // K) + ((head_dim * num_kv_heads) // M) * ( hidden_size// K) * 2
        overall_operation_amount    += operation_amount
        attainable_operation        += operation_amount * (M * K * batch_size)
        theoretical_operation       += operation_amount * (M * K * N)

        # QKT
        operation_amount =  batch_size * num_attn_heads * (head_dim // K) * (context_len // M)
        overall_operation_amount    += operation_amount
        attainable_operation        += operation_amount * (M * K)
        theoretical_operation       += operation_amount * (M * K * N)

        # PV
        operation_amount =  batch_size * num_attn_heads * (context_len // K) * (head_dim // M)
        overall_operation_amount    += operation_amount
        attainable_operation        += operation_amount * (M * K)
        theoretical_operation       += operation_amount * (M * K * N)
    
    return [operation_amount, attainable_operation, theoretical_operation]



def _report_embedding_utilization(model_info: Dict[str, Any], mode: str, input_token_len: int, M: int, N: int, K: int) -> None:
    """
    Report the utilization of flash attention for a given node.
    """
    
    batch_size = model_info["batch_size"]
    hidden_size = 8192

    theoretical_operation = 0
    attainable_operation = 0

    if mode == "prefilling":
        operation_amount = (hidden_size // M) * (hidden_size // K) * (input_token_len // N)
        attainable_operation += operation_amount * (M * K * N)
        theoretical_operation += operation_amount * (M * K * N)
    else:
        # Assuming Decoding only
        operation_amount = (hidden_size // M) * (hidden_size // K)
        attainable_operation += operation_amount * (M * K * batch_size)
        theoretical_operation += operation_amount * (M * K * N)

    return [operation_amount, attainable_operation, theoretical_operation]



def _report_ffn_utilization( model_info: Dict[str, Any], mode: str, input_token_len: int, M: int, N: int, K: int) -> None:
    
    """
    Report the utilization of flash attention for a given node.
    """

    batch_size = model_info["batch_size"]
    hidden_size = 8192
    intermediate_size = 28672
    overall_operation_amount = 0
    theoretical_operation = 0
    attainable_operation = 0

    if mode == "prefilling":
        # Up Projection
        operation_amount = (intermediate_size // M) * (hidden_size // K) * (input_token_len // N)
        overall_operation_amount += operation_amount
        attainable_operation += operation_amount * (M * K * N)
        theoretical_operation += operation_amount * (M * K * N)

        # Gate Projection
        operation_amount = (intermediate_size // M) * (hidden_size // K) * (input_token_len // N)
        overall_operation_amount += operation_amount
        attainable_operation += operation_amount * (M * K * N)
        theoretical_operation += operation_amount * (M * K * N)

        # Down Projection
        operation_amount = (hidden_size // M) * (intermediate_size // K) * (input_token_len // N)
        overall_operation_amount += operation_amount
        attainable_operation += operation_amount * (M * K * N)
        theoretical_operation += operation_amount * (M * K * N)
    else:
        # Decoding
        # Up Projection
        operation_amount = (intermediate_size // M) * (hidden_size // K)
        overall_operation_amount += operation_amount
        attainable_operation += operation_amount * (M * K * batch_size)
        theoretical_operation += operation_amount * (M * K * N)

        # Gate Projection
        operation_amount = (intermediate_size // M) * (hidden_size // K)
        overall_operation_amount += operation_amount
        attainable_operation += operation_amount * (M * K * batch_size)
        theoretical_operation += operation_amount * (M * K * N)

        # Down Projection
        operation_amount = (hidden_size // M) * (intermediate_size // K)
        overall_operation_amount += operation_amount
        attainable_operation += operation_amount * (M * K * batch_size)
        theoretical_operation += operation_amount * (M * K * N)

    return [overall_operation_amount, attainable_operation, theoretical_operation]


    
def _report_lm_head_utilization(model_info: Dict[str, Any], M: int, K: int, N: int) -> str:
    """
    Report the utilization of LM head for a given node.
    """
    batch_size = model_info["batch_size"]
    vocab_size = model_info.get("vocab_size", 128256)
    hidden_size = 8192

    theoretical_operation = 0
    attainable_operation = 0

    # Assuming Decoding only
    operation_amount = (vocab_size // M) * (hidden_size // K)
    attainable_operation += operation_amount * (M * K * batch_size)
    theoretical_operation += operation_amount * (M * K * N)

    return [operation_amount, attainable_operation, theoretical_operation]
    


def analyse_overall_utilization(model_info: Dict[str, Any], mode:str, M: int, K: int, N: int) -> str:
    """
    Transform the complete symbolic graph into assembly code.

    Args:
        symbolic_graph: The symbolic graph from LLMModelParser
        model_info: Model metadata for header generation

    Returns:
        Complete assembly program as string
    """


    overall_operations = {"embedding": 0, "attention": 0, "ffn": 0, "lm_head": 0}
    overall_attainable_FLOPS = {"embedding": 0, "attention": 0, "ffn": 0, "lm_head": 0}
    overall_theoretical_FLOPS = {"embedding": 0, "attention": 0, "ffn": 0, "lm_head": 0}
    layer_num = model_info.get("layer_num", 1)


    # Generate code for each node in execution order
    operation_type = "embedding"
    single_op_operation = _report_embedding_utilization( model_info, mode, 0, M, K, N)
    overall_operations[operation_type] += single_op_operation[0]
    overall_attainable_FLOPS[operation_type] += single_op_operation[1]
    overall_theoretical_FLOPS[operation_type] += single_op_operation[2]
   
    for layer in range(layer_num):
        single_op_operation = _report_flash_attn_utilization(model_info, mode, 0, M, K, N)
        overall_operations["attention"]         += single_op_operation[0]
        overall_attainable_FLOPS["attention"]   += single_op_operation[1]
        overall_theoretical_FLOPS["attention"]  += single_op_operation[2]
        single_op_operation = _report_ffn_utilization(model_info, mode, 0, M, K, N)
        overall_operations["ffn"]               += single_op_operation[0]
        overall_attainable_FLOPS["ffn"]         += single_op_operation[1]
        overall_theoretical_FLOPS["ffn"]        += single_op_operation[2]

    single_op_operation = _report_lm_head_utilization(model_info, M, K, N)
    overall_operations["lm_head"]               += single_op_operation[0]
    overall_attainable_FLOPS["lm_head"]        += single_op_operation[1]
    overall_theoretical_FLOPS["lm_head"]       += single_op_operation[2]

    return {
        "operations": overall_operations,
        "attainable_FLOPS": overall_attainable_FLOPS,
        "theoretical_FLOPS": overall_theoretical_FLOPS
    }
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    colors = {
        "c1": tuple(i / 255 for i in (247, 252, 240)),
        "c2": tuple(i / 255 for i in (224, 243, 219)),
        "c3": tuple(i / 255 for i in (204, 235, 197)),
        "c4": tuple(i / 255 for i in (168, 221, 181)),
        "c5": tuple(i / 255 for i in (123, 204, 196)),
        "c6": tuple(i / 255 for i in (78, 179, 211)),
        "c7": tuple(i / 255 for i in (43, 140, 190)),
        "c8": tuple(i / 255 for i in (8, 88, 158)),
        "red" : tuple(i / 255 for i in (190, 195, 137))
    }
    
    analyse_result = {}
    mode = "decoding"
    context_len = 512
    model_info = {
        "batch_size": 8,
        "vocab_size": 128256,
        "hidden_size": 8192,
        "layer_num": 80
    }
    M = 64
    K = 64
    N = 64
    
    while context_len <= 128000:
        model_info["context_len"] = context_len
        context_len *= 2
        analyse_result[context_len] = {}
        analyse_result[context_len]["flops"] = analyse_overall_utilization(model_info, mode, M, K, N)["operations"]
        analyse_result[context_len]["kv_cache"] = (
            2 * 40 * model_info["context_len"] * 8 * 128 * 2 * (model_info["batch_size"])
        ) / (1024**3) 
        print(f"Context Length: {context_len}, KV Cache: {analyse_result[context_len]['kv_cache']} GB")

    data = analyse_result
    seq_lens = sorted(data.keys())
    attn_pct = []
    ffn_pct = []
    kv_pct = []

    for seq in seq_lens:
        flops = data[seq]['flops']
        total_flops = sum(flops.values())
        attn_pct.append(100 * flops['attention'] / total_flops)
        ffn_pct.append(100 * flops['ffn'] / total_flops)
        kv_pct.append( data[seq]['kv_cache'])  # percentage of 144GB

    # 70B model weight usage (FP16 = 2 bytes per param)
    model_params = 70e9  # 70B
    fp16_size_bytes = model_params * 2
    fp16_size_gb = fp16_size_bytes / (1024**3)  # in GB

    seq_lens_k = [s // 1024 for s in seq_lens]

    # === Plot 1: FLOPs breakdown ===
    fig1, ax1 = plt.subplots(figsize=(5, 3.5))
    ax1.plot(seq_lens_k, attn_pct, marker='o', label='Attention FLOPs', color=colors['c4'])
    ax1.plot(seq_lens_k, ffn_pct, marker='s', label='FFN FLOPs', color=colors['c6'])
    ax1.set_xlabel('Number of Tokens', fontsize=12)
    ax1.set_ylabel('FLOPs Breakdown (%)', fontsize=12)
    ax1.set_xscale('log', base=2)
    ax1.set_xticks(seq_lens_k)
    ax1.set_xticklabels([f"{x}K" for x in seq_lens_k], fontsize=12)
    ax1.tick_params(axis='y', labelsize=12)
    ax1.tick_params(axis='x', labelsize=12)
    ax1.set_title('FLOPs Breakdown (Batch Size = 4)', fontsize=12)
    ax1.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax1.legend(fontsize=12, loc='lower center', ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.5),)
    plt.tight_layout()
    plt.savefig("flops_breakdown.png", dpi=300, bbox_inches='tight', transparent=True)

    # === Plot 2: HBM utilisation ===
    fig2, ax2 = plt.subplots(figsize=(5, 3.5))
    ax2.plot(seq_lens_k, kv_pct, marker='^', label='KV Cache', color=colors['c8'])
    ax2.set_xlabel('Number of Tokens', fontsize=12)
    ax2.set_ylabel('Memory Usage (GB)', fontsize=12)
    ax2.set_xscale('log', base=2)
    ax2.set_xticks(seq_lens_k)
    ax2.set_xticklabels([f"{x}K" for x in seq_lens_k], fontsize=12)
    ax2.hlines(59, xmin=seq_lens_k[0], xmax=seq_lens_k[-1], colors=colors["red"], linestyles='--', label='Model Weight')
    ax2.tick_params(axis='y', labelsize=12)
    ax2.tick_params(axis='x', labelsize=12)
    ax2.set_title('Memory Usage (Batch Size = 4)', fontsize=12)
    ax2.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax2.legend(loc='lower center', ncol=2, fontsize=12, frameon=False, bbox_to_anchor=(0.5, -0.5))
    plt.tight_layout()
    plt.savefig("hbm_utilization.png", dpi=300, bbox_inches='tight', transparent=True)
