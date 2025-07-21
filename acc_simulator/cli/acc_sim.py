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
"""

from pprint import pformat
from typing import Literal, Union
import time

import torch

from ..quantize.quantized_layers import MXFPLinearPTQ, MXFPEmbeddingPTQ, FPRMSNormPTQ
from ..models.llama_quantized import LlamaAttentionMXFP, LlamaMLPActFP
from ..eval.eval_utils import *
from ..eval import evaluate_with_lm_eval, evaluate_perplexity

from ..utils import setup_args_linear_nonlinear, replace_modules, create_device_map
from torch import nn
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.models.llama.modeling_llama import (
    LlamaAttention,
    LlamaRMSNorm,
    LlamaMLP
)
from accelerate import dispatch_model


def llama_eval(
    # Use Meta 3 hf checkpoints to match with SOTA paper: meta-llama/Meta-Llama-3-nB
    model_name: str = "meta-llama/Meta-Llama-3-8B",
    tasks: Union[str, list[str]] = "wikitext",
    preset: Union[str, None] = "original",
    preset_mxfp_X: Union[str, None] = None,
    preset_mxfp_W: Union[str, None] = None,
    preset_mxfp_Kv: Union[str, None] = None,
    preset_minifloat_NL: Union[str, None] = None,
    model_parallel: bool = True,
    log_dir: Union[str, None] = None,
    enable_eval_harness: bool = False
):
    """
    Evaluate the perplexity of a model on lm-eval tasks with MXFP and minifloat quantization
    applied to attention, MLP, normalization, and embedding layers.

    If a preset is specified, it sets default quantization metadata based on predefined formats;
    otherwise, no quantization is applied.

    Args:
        model_name (str): HuggingFace model ID.
        tasks (str or list): lm-eval task(s) to run.
        preset (str): Quantization preset, e.g., "XqWqBqKVqNLq" enables quantization of inputs (Xq), weights (Wq), biases (Bq), KV cache (KVq) and Non linear Ops(NLq). Use "original" to disable all quantization.
        preset_mxfp_X (str): MXFP format for activations. Expected format: MXFP_E<exp>M<frac>_B<block>_S<scale>
        preset_mxfp_W (str): MXFP format for weights. Expected format: MXFP_E<exp>M<frac>_B<block>_S<scale>
        preset_mxfp_Kv (str): MXFP format for KV cache. Expected format: MXFP_E<exp>M<frac>_B<block>_S<scale>
        preset_minifloat_NL (str): Minifloat format for nonlinear ops. Expected format: FP_E<exp>M<frac>[_B<bias>]
        model_parallel: Whether to auto-dispatch model across GPUs, will trigger Triton Kernel for mxfp quantization if set.
        log_dir: Directory to save logs and results.
        enable_eval_harness: Whether to run evaluation via EleutherAI lm-eval-harness.
    """
    start_time = time.time()
    preset_mxfp_X, preset_mxfp_W, preset_mxfp_Kv, preset_minifloat_NL = validate_and_sanitize_quant_args(
        preset,
        preset_mxfp_X,
        preset_mxfp_W,
        preset_mxfp_Kv,
        preset_minifloat_NL
    )

    quant_args = setup_args_linear_nonlinear(preset, preset_mxfp_X, preset_mxfp_W,  preset_mxfp_Kv, preset_minifloat_NL)

    if log_dir:
        log_dir = create_experiment_log_dir(log_dir)
        full_args = locals().copy()         
        full_args["quant_args"] = quant_args 
        save_args(log_dir, full_args)

    if preset != "original":
        print(f"Using preset {preset}, which sets the following parameters:\n")
        # for k, v in quant_args.items():
        #     print(f"{k}:\n{pformat(v)}")
    else:
        print("Using original parameters, no quantization applied.")

    
    # create the tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(
        model_name, use_fast=False, trust_remote_code=True
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, attn_implementation="eager"
    )
    if model_parallel:
        device_map = create_device_map(model, "auto-balanced")
        model = dispatch_model(model, device_map=device_map)
    else: 
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = model.to(device)
    
    if preset != "original":
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
        replace_modules(
            model,
            target_class=nn.Linear,
            replacement_class=MXFPLinearPTQ,
            factory_fn=MXFPLinearPTQ.from_linear,
            kwargs=quant_args["fc_kwargs"],
            label="MXFPLinearPTQ"
        )

        # Embedding
        replace_modules(
            model,
            target_class=nn.Embedding,
            replacement_class=MXFPEmbeddingPTQ,
            factory_fn=MXFPEmbeddingPTQ.from_embedding,
            kwargs=quant_args["embed_kwargs"],
            label="Embedding"
        )

        # RMSNorm
        replace_modules(
            model,
            target_class=LlamaRMSNorm,
            replacement_class=FPRMSNormPTQ,
            factory_fn=FPRMSNormPTQ.from_rmsnorm,
            kwargs=quant_args["rms_kwargs"],
            label="FPRMSNormPTQ"
        )
    
    if enable_eval_harness:
        results = evaluate_with_lm_eval(
            model=model, 
            tokenizer=tokenizer, 
            tasks=tasks, 
            max_length=2048, 
            batch_size="auto", 
            log_samples=False)
    else:
        results = evaluate_perplexity(
            model=model, 
            tokenizer=tokenizer, 
            dataset_name=tasks, 
            max_length=2048)

    if log_dir:
        save_results(log_dir, results)

    total_time = time.time() - start_time
    print(f"\n[INFO] Total workload time: {total_time:.2f} seconds")
    return results

if __name__ == "__main__":
    import time
    from jsonargparse import CLI

    start_time = time.time()
    CLI(llama_eval)
    total_time = time.time() - start_time
    print(f"\n[INFO] Total workload time: {total_time:.2f} seconds")
