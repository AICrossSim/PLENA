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

from typing import Union
import time

import torch
import transformers

from ..eval.eval_utils import validate_and_sanitize_quant_args, create_experiment_log_dir, save_args, save_results, quantize_model, setup_model
from ..eval import evaluate_with_lm_eval, evaluate_perplexity
from ..utils import setup_args_linear_nonlinear
from ..rotation import rotate_llama, fuse_rms_norms, replace_rms_norms

def llama_eval(
    # Use Meta 3 hf checkpoints to match with SOTA paper: meta-llama/Meta-Llama-3-nB
    model_name: str = "meta-llama/Meta-Llama-3-8B",
    tasks: Union[str, list[str]] = "wikitext",
    preset: Union[str, None] = "original",
    preset_mxfp_X: Union[str, None] = None,
    preset_mxfp_W: Union[str, None] = None,
    preset_mxint_W: Union[str, None] = None,
    preset_mxfp_Kv: Union[str, None] = None,
    preset_minifloat_NL: Union[str, None] = None,
    model_parallel: bool = True,
    log_dir: Union[str, None] = None,
    enable_eval_harness: bool = False,
    use_gptq: bool = False,
    offline_rotate: bool = False,
    online_rotate: bool = False
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
        use_gptq (bool): Whether to use GPTQ optimization during quantization.
            When True, collects input Hessians and applies GPTQ algorithm.
            When False, performs simple cast to MXFP format.
            Defaults to True.
        offline_rotate: Whether to apply offline hadamard rotation.
        online_rotate: Whether to apply online inner layer activation rotation.
    """
    start_time = time.time()
    preset_mxfp_X, preset_mxfp_W, preset_mxint_W, preset_mxfp_Kv, preset_minifloat_NL = validate_and_sanitize_quant_args(
        preset,
        preset_mxfp_X,
        preset_mxfp_W,
        preset_mxint_W,
        preset_mxfp_Kv,
        preset_minifloat_NL
    )

    quant_args = setup_args_linear_nonlinear(preset, preset_mxfp_X, preset_mxfp_W,  preset_mxint_W, preset_mxfp_Kv, preset_minifloat_NL, online_rotate)

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

    tokenizer, model = setup_model(model_name, model_parallel, dtype=torch.float16)
    
    # TODO: set seed properly later, also seed the calibration samples
    transformers.set_seed(0)
    model.eval()
    if offline_rotate:
        fuse_rms_norms(model)
        replace_rms_norms(model)
        rotate_llama(model, online_rotate) 
        if online_rotate:
            quantize_model(model=model, quant_args=quant_args, linear_only=True, skip_lm_head=False)
    
    quantize_model(model=model, quant_args=quant_args, linear_only=True, skip_lm_head=False)
    
    if preset != "original":
        # TODO: Quantization Holder
        if use_gptq:
            pass
        else:
            # Cast without GPTQ
            pass


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
            max_length=2048,
            verbose=True)

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