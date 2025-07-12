"""
This script performs MXFP quantization on LLaMA models and evaluates their performance using lm-eval.

Supported quantization currently:
mxfp format:
- Linear weights (nn.Linear)
- Attention activations (QK^T, AV)
- KV cache
- Embedding layers
minifloat format:
- MLP (SiLU)
- ROPE
- Attention (Softmax)
- RMSNorm

Evaluation is done via EleutherAI's lm-eval harness on tasks like Wikitext.

Usage:
    python -m acc_simulator.eval.acc_sim --help

Examples:
    # Full quantization of weights, bias, activations, and KV cache, rope, and non-linear ops
    python -m acc_simulator.eval.acc_sim --preset XqWqBqKVq --preset_mxfp_X MXFP8_E4M3 --preset_mxfp_W MXFP8_E4M3 --preset_minifloat FP8_E4M3

    # No quantization (baseline)
    python -m acc_simulator.eval.acc_sim --preset original

"""

from pprint import pformat
from typing import Literal, Union
import time

import torch
from lm_eval.evaluator import simple_evaluate
from lm_eval.models.huggingface import HFLM
from lm_eval.utils import make_table

from ..quantize.quantized_layers import MXFPLinearPTQ, MXFPEmbeddingPTQ, FPRMSNormPTQ
from ..models.llama_quantized import LlamaAttentionMXFP, LlamaMLPActFP
from .eval_utils import *

from ..utils import setup_args_linear_nonlinear, replace_modules, create_device_map
from torch import nn
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.models.llama.modeling_llama import (
    LlamaAttention,
    LlamaRMSNorm,
    LlamaMLP
)
from accelerate import dispatch_model


def mxfp_lm_eval(
    # meta-llama/Llama-3.2-1B
    model_name: str = "meta-llama/Llama-3.1-70B",
    tasks: Union[str, list[str]] = "wikitext",
    preset: Union[ Literal["XqWqBqKVq", "XWqBqKV", "XWqBqKVq", "original"], None] = "XqWqBqKVq",
    preset_mxfp_X: Union[Literal["MXFP8_E4M3", "MXFP8_E5M2", "MXFP6_E2M3", "MXFP6_E3M2", "MXFP4_E2M1"], None] = None,
    preset_mxfp_W: Union[Literal["MXFP8_E4M3", "MXFP8_E5M2", "MXFP6_E2M3", "MXFP6_E3M2", "MXFP4_E2M1"], None] = None,
    preset_mxfp_Kv: Union[Literal["MXFP8_E4M3", "MXFP8_E5M2", "MXFP6_E2M3", "MXFP6_E3M2", "MXFP4_E2M1"], None] = None,
    preset_minifloat: Union[Literal["FP8_E4M3", "FP8_E5M2"], None] = None,
    model_parallel: bool = True,
    log_base_dir: Union[str, None] = "logs"
):
    """
    Evaluate the perplexity of a model on lm-eval tasks with MXFP and minifloat quantization
    applied to attention, MLP, normalization, and embedding layers.

    If a preset is specified, it sets default quantization metadata based on predefined formats;
    otherwise, no quantization is applied.

    Args:
        model_name (str): HuggingFace model ID.
        tasks (str or list): lm-eval task(s) to run.
        preset (str): Quantization preset, e.g., "XqWqBqKVq" or "original".
        preset_mxfp_X (str): MXFP format for activations.
        preset_mxfp_W (str): MXFP format for weights.
        preset_minifloat (str): Minifloat format for nonlinear ops (e.g., SiLU, softmax).
    """

    quant_args = setup_args_linear_nonlinear(preset, preset_mxfp_X, preset_mxfp_W,  preset_mxfp_Kv, preset_minifloat)

    log_dir = create_experiment_log_dir(log_base_dir)
    full_args = locals().copy()         
    full_args["quant_args"] = quant_args 
    save_args(log_dir, full_args)

    if preset != "original":
        print(f"Using preset {preset}, which sets the following parameters:\n")
        for k, v in quant_args.items():
            print(f"{k}:\n{pformat(v)}")
    else:
        print("Using original parameters, no quantization applied.")

    
    # create the tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, attn_implementation="eager"
    )
    if model_parallel:
        device_map = create_device_map(model, "auto-balanced")
        model = dispatch_model(model, device_map=device_map)
    else: 
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = model.to(device)
    
    # MLP - SILU
    replace_modules(
        model,
        target_class=LlamaMLP,
        replacement_class=LlamaMLPActFP,
        factory_fn=LlamaMLPActFP.from_mlp,
        kwargs=quant_args["mlp_kwargs"],
        label="LlamaMLP"
    )

    # Attention - softmax, rope, matmul
    replace_modules(
        model,
        target_class=LlamaAttention,
        replacement_class=LlamaAttentionMXFP,
        factory_fn=LlamaAttentionMXFP.from_attention,
        kwargs=quant_args["attn_kwargs"],
        label="LlamaAttention"
    )

    # Linear
    # replace_modules(
    #     model,
    #     target_class=nn.Linear,
    #     replacement_class=MXFPLinearPTQ,
    #     factory_fn=MXFPLinearPTQ.from_linear,
    #     kwargs=quant_args["fc_kwargs"],
    #     label="MXFPLinearPTQ"
    # )

    # # Embedding
    # replace_modules(
    #     model,
    #     target_class=nn.Embedding,
    #     replacement_class=MXFPEmbeddingPTQ,
    #     factory_fn=MXFPEmbeddingPTQ.from_embedding,
    #     kwargs=quant_args["embed_kwargs"],
    #     label="Embedding"
    # )

    # RMSNorm
    # replace_modules(
    #     model,
    #     target_class=LlamaRMSNorm,
    #     replacement_class=FPRMSNormPTQ,
    #     factory_fn=FPRMSNormPTQ.from_rmsnorm,
    #     kwargs=quant_args["rms_kwargs"],
    #     label="FPRMSNormPTQ"
    # )

    # Wrap and evaluate
    model_lm_eval = HFLM(pretrained=model, tokenizer=tokenizer, max_length=2048)
    if isinstance(tasks, str):
        tasks = [tasks]

    results = simple_evaluate(
        model=model_lm_eval,
        tasks=tasks,
        batch_size="auto",
        log_samples=False
    )

    save_results(log_dir, results)

    table = make_table(results)
    print(table)
    print(f"[INFO] Results saved in {log_dir}")


if __name__ == "__main__":
    import time
    from jsonargparse import CLI

    start_time = time.time()
    CLI(mxfp_lm_eval)
    total_time = time.time() - start_time
    print(f"\n[INFO] Total workload time: {total_time:.2f} seconds")
