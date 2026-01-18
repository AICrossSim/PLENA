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
from pathlib import Path
import time
import logging

import torch
import transformers

from ..eval.ar_model.eval_utils import validate_and_sanitize_quant_args, create_experiment_log_dir, save_args, save_results, quantize_model, setup_model, move_to_gpu, load_gptq, save_gptq
from ..eval.ar_model import evaluate_with_lm_eval, evaluate_perplexity
from ..utils import setup_args_linear_nonlinear
from ..rotation import rotate_llama, fuse_rms_norms, replace_rms_norms
from ..gptq import quantize_model_gptq, get_loaders
from ..utils import get_logger, set_logging_verbosity

logger = get_logger(__name__)
set_logging_verbosity("debug")

def llama_eval(
    # Use Meta 3 hf checkpoints to match with SOTA paper: meta-llama/Meta-Llama-3-nB
    model_name: str = "meta-llama/Meta-Llama-3-8B",
    tasks: Union[str, list[str]] = "wikitext",
    preset: Union[str, None] = "original",
    preset_X: Union[str, None] = None,
    preset_W: Union[str, None] = None,
    preset_Kv: Union[str, None] = None,
    preset_NL: Union[str, None] = None,
    device_id: str = None,
    model_parallel: bool = False,
    log_dir: Union[str, None] = None,
    enable_eval_harness: bool = False,
    use_gptq: bool = False,
    offline_rotate: bool = False,
    online_rotate: bool = False,
    layer_for_online_rotate: Union[str, None] = None,
    clip_search: bool = False,
    clip_search_y: bool = False,
    seqlen: int = 2048,
    save_gptq_model: bool = False,
    cali_batch_size: int = 8,
    save_dir: str = None,
    resume_from_checkpoint: Union[str, None] = None,

    full_system_sim: bool = False,
    # gptq_ckpt_dir: Union[str, None] = None,

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
        preset_X (str): Quantization format for activations. Expected format: MXFP_E<exp>M<frac>_B<block>_S<scale>
        preset_W (str): Quantization format for weights. Expected format: MXFP_E<exp>M<frac>_B<block>_S<scale>
        preset_Kv (str): Quantization format for KV cache. Expected format: MXFP_E<exp>M<frac>_B<block>_S<scale>
        preset_NL (str): Quantization format for nonlinear ops. Expected format: FP_E<exp>M<frac>[_B<bias>]
        model_parallel: Whether to auto-dispatch model across GPUs, will trigger Triton Kernel for mxfp quantization if set.
        log_dir: Directory to save logs and results.
        enable_eval_harness: Whether to run evaluation via EleutherAI lm-eval-harness.
        use_gptq (bool): Whether to use GPTQ optimization during quantization.
            When True, collects input Hessians and applies GPTQ algorithm.
            When False, performs simple cast to MXFP format.
            Defaults to True.
        offline_rotate: Whether to apply offline hadamard rotation.
        online_rotate: Whether to apply online inner layer activation rotation.
        layer_for_online_rotate: The layer to apply online inner layer activation rotation.
        clip_search_y: Set True to enable linear W clip search based on output, default False to search clipping based on l2(W, Wq).
        cali_batch_size: The batch size used to matmul the calibration set with sliced W block for quantization error search. Could play with this if your Vram is sufficient.
        save_dir (str): Directory to save/load quantization checkpoints. Enables automatic checkpoint saving after each layer.
        resume_from_checkpoint (str): Resume quantization from checkpoint. Use 'latest' to automatically find the latest checkpoint, or provide a specific checkpoint file path.
    """
    preset_X, preset_W, preset_Kv, preset_NL = validate_and_sanitize_quant_args(
        preset,
        preset_X,
        preset_W,
        preset_Kv,
        preset_NL
    )

    quant_args = setup_args_linear_nonlinear(preset, preset_X, preset_W, preset_Kv, preset_NL, online_rotate, clip_search_y)

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

    transformers.set_seed(0)
    # TODO: set the model path to the models checkpoints already stored inside .data/models/hw1020/
    tokenizer, model = setup_model(model_name, model_parallel, dtype=torch.float16, 
                                   device=device_id if not model_parallel else None)
    # breakpoint()
    model.eval()

    if preset != "original":
        # TODO: Quantization Holder
        if use_gptq:
            # TODO: deal with args later on
            logger.info(f"Getting loaders")
            trainloader = get_loaders(
                "wikitext2", nsamples=128,
                seed=0, model=model_name,
                seqlen=seqlen, eval_mode=False
            )
            logger.info(f"Loaders got")
            # GPTQ first quantize and repalce linear, 
            # move each decoder block on gpu to quantize, 
            # disable model parallel for gptq for now, hence use model's device rn.
            if clip_search:
                if clip_search_y:
                    checkpoint_dir = f"{save_dir}/ckpts_y_search/{model_name.replace('/', '_')}"
                else:
                    checkpoint_dir = f"{save_dir}/ckpts_w_search/{model_name.replace('/', '_')}"
            else:
                checkpoint_dir = f"{save_dir}/ckpts_no_search/{model_name.replace('/', '_')}"
            # ckpt_dir = Path(checkpoint_dir) / model_name.replace('/', '_')
            # ckpt_file = ckpt_dir / "model.safetensors"
            # if ckpt_file.exists():
            #     print(f"Loading GPTQ model from {ckpt_file}")
            #     model=load_gptq(model, ckpt_dir)
            # else:
                # load the model on cpu before gptq, device_id is used to load model decoder layer on gpu, once per layer.
            # model.to("cpu")
            logger.info(f"Quantizing GPTQ")
            start_time = time.time()
            quantize_model_gptq(model=model, dataloader=trainloader, quant_args=quant_args, clip_search=clip_search, dev=device_id, save_q_model=True, cali_batch_size = cali_batch_size, checkpoint_dir=checkpoint_dir, resume_from_checkpoint=resume_from_checkpoint)
            logger.info(f"GPTQ quantized")
            logger.info(f"Time taken to quantize GPTQ: {time.time() - start_time} seconds")
            # right now always save the weights after gptq, and not rewrite
            if model_parallel:
                logger.info(f"Model device: {model.device}")
                model=move_to_gpu(model, model_parallel)
                logger.info(f"Model moved to GPU: {model.device}")
            else:
                model.to(device_id)
            quantize_model(model=model, quant_args=quant_args, linear_quantized=True, full_system_sim=False, online_rotate=online_rotate, clip_search=clip_search, layer_for_online_rotate=layer_for_online_rotate)
        else:
            # Direct cast without GPTQ, round-to-nearest mode
            if model_parallel:
                model=move_to_gpu(model, model_parallel)
                # logger.info(f"Model moved to GPU: {model.device}")
            else:
                model.to(device_id)
            quantize_model(model=model, quant_args=quant_args, linear_quantized=False, online_rotate=online_rotate, clip_search=clip_search, layer_for_online_rotate=layer_for_online_rotate)


    if enable_eval_harness:
        results = evaluate_with_lm_eval(
            model=model, 
            tokenizer=tokenizer, 
            tasks=tasks, 
            max_length=seqlen, 
            batch_size="auto", 
            log_samples=False)
    else:
        results = evaluate_perplexity(
            model=model, 
            tokenizer=tokenizer, 
            dataset_name=tasks, 
            max_length=seqlen,
            verbose=True)

    if log_dir:
        save_results(log_dir, results)

    return results

if __name__ == "__main__":
    import time
    from jsonargparse import CLI

    start_time = time.time()
    CLI(llama_eval)
    total_time = time.time() - start_time
    print(f"\n[INFO] Total workload time: {total_time:.2f} seconds")