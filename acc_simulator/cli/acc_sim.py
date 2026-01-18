"""
Unified quantization and evaluation for AR (LLaMA) and dLLM (Fast-dLLM) models.

Supported quantization:
- mxfp format: Linear weights, Attention activations, KV cache, Embedding layers
- minifloat format: MLP (SiLU), ROPE, Attention (Softmax), RMSNorm

Usage:
    python -m acc_simulator.cli.acc_sim --help

Example (AR model):
    python -m acc_simulator.cli.acc_sim --model_name meta-llama/Meta-Llama-3-8B --tasks wikitext

Example (dLLM model):
    python -m acc_simulator.cli.acc_sim --model_type dllm \
        --model_name Efficient-Large-Model/Fast_dLLM_v2_1.5B \
        --tasks gsm8k --preset XWqBKVNL --preset_W MXINT_4_B32_S8
"""

from typing import Union, Literal
from pathlib import Path
import time
import types

import torch
import transformers
from torch import nn

from ..eval.eval_utils import (
    validate_and_sanitize_quant_args, create_experiment_log_dir,
    save_args, save_results, quantize_model, setup_model, move_to_gpu,
    load_gptq, save_gptq
)
from ..eval.ar_model import evaluate_with_lm_eval, evaluate_perplexity
from ..utils import setup_args_linear_nonlinear
from ..rotation import rotate_llama, fuse_rms_norms, replace_rms_norms
from ..gptq import quantize_model_gptq, get_loaders
from ..utils import get_logger, set_logging_verbosity
from ..quantize.quantized_layers.linear import MXFPLinearPTQ

logger = get_logger(__name__)
set_logging_verbosity("debug")


def quantize_linear_layers_only(
    model: nn.Module,
    quant_args: dict,
    skip_lm_head: bool = True,
    clip_search: bool = False,
):
    """
    Replace only nn.Linear layers with MXFPLinearPTQ.
    Used for dLLM models where we don't want to replace attention/MLP modules.
    """
    fc_kwargs = quant_args.get("fc_kwargs", {})
    fc_kwargs["clip_search"] = clip_search

    linear_count = sum(1 for _, m in model.named_modules() if isinstance(m, nn.Linear))
    print(f"Found {linear_count} nn.Linear layers")

    replaced = 0
    for name, module in list(model.named_modules()):
        if isinstance(module, nn.Linear):
            if skip_lm_head and "lm_head" in name:
                print(f"Skipping: {name}")
                continue

            parts = name.rsplit(".", 1)
            if len(parts) == 2:
                parent = model.get_submodule(parts[0])
                attr_name = parts[1]
            else:
                parent = model
                attr_name = name

            new_layer = MXFPLinearPTQ.from_linear(module, **fc_kwargs)
            setattr(parent, attr_name, new_layer)
            replaced += 1

    print(f"Quantized {replaced} Linear layers")
    return model


def acc_sim_eval(
    # Model settings
    model_name: str = "meta-llama/Meta-Llama-3-8B",
    model_type: Literal["ar", "dllm"] = "ar",
    tasks: Union[str, list[str]] = "wikitext",
    device_id: str = "cuda:0",
    batch_size: int = 32,

    # Quantization settings (shared)
    preset: Union[str, None] = "original",
    preset_X: Union[str, None] = None,
    preset_W: Union[str, None] = None,
    preset_Kv: Union[str, None] = None,
    preset_NL: Union[str, None] = None,
    clip_search: bool = False,
    clip_search_y: bool = False,
    online_rotate: bool = False,
    layer_for_online_rotate: Union[str, None] = None,

    # AR-specific settings
    model_parallel: bool = False,
    enable_eval_harness: bool = False,
    use_gptq: bool = False,
    offline_rotate: bool = False,
    seqlen: int = 2048,
    save_gptq_model: bool = False,
    cali_batch_size: int = 8,
    save_dir: str = None,
    resume_from_checkpoint: Union[str, None] = None,
    full_system_sim: bool = False,

    # dLLM-specific settings
    mask_id: int = 151665,
    bd_size: int = 32,
    small_block_size: int = 8,
    threshold: float = 1.0,
    max_new_tokens: int = 2048,
    num_fewshot: int = 0,
    show_speed: bool = True,

    # Logging
    log_dir: Union[str, None] = None,
):
    """
    Unified evaluation for AR and dLLM models with MXFP/minifloat quantization.

    Args:
        model_name: HuggingFace model ID
        model_type: "ar" for autoregressive (LLaMA), "dllm" for diffusion LLM
        tasks: lm-eval task(s) to run
        device_id: CUDA device
        batch_size: Batch size for evaluation

        # Quantization (shared)
        preset: Quantization preset (e.g., "XWqBKVNL")
        preset_X: Activation quantization format
        preset_W: Weight quantization format (e.g., "MXINT_4_B32_S8")
        preset_Kv: KV cache quantization format
        preset_NL: Non-linear ops quantization format
        clip_search: Enable clip search
        clip_search_y: Use output-based clip search
        online_rotate: Enable online rotation

        # AR-specific
        model_parallel: Auto-dispatch across GPUs
        enable_eval_harness: Use lm-eval harness (AR only)
        use_gptq: Use GPTQ optimization (AR only)
        seqlen: Sequence length

        # dLLM-specific
        mask_id: Mask token ID for dLLM
        bd_size: Block diffusion size
        threshold: Unmasking threshold
        max_new_tokens: Max tokens to generate
        num_fewshot: Few-shot examples
        show_speed: Show throughput metrics

        log_dir: Directory to save logs
    """
    print("=" * 60)
    print(f"Model Evaluation ({model_type.upper()})")
    print("=" * 60)
    print(f"Model: {model_name}")
    print(f"Tasks: {tasks}")

    # Validate and setup quantization args
    if preset and preset != "original":
        preset_X, preset_W, preset_Kv, preset_NL = validate_and_sanitize_quant_args(
            preset, preset_X, preset_W, preset_Kv, preset_NL
        )
        quant_args = setup_args_linear_nonlinear(
            preset, preset_X, preset_W, preset_Kv, preset_NL,
            online_rotate, clip_search_y
        )
        print(f"Quantization: {preset}")
        print(f"  preset_W: {preset_W}, preset_X: {preset_X}")
    else:
        quant_args = None
        print("Quantization: None (original)")
    print("=" * 60)

    if log_dir:
        log_dir = create_experiment_log_dir(log_dir)
        full_args = locals().copy()
        full_args["quant_args"] = quant_args
        save_args(log_dir, full_args)

    transformers.set_seed(0)

    # === dLLM path ===
    if model_type == "dllm":
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from lm_eval import evaluator
        from ..eval.dllm import generation_functions

        # Import the eval harness from dllm_sim
        from .dllm_sim import FastDLLMEvalHarness

        print(f"\nLoading dLLM model from {model_name}...")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
        )
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

        model.eval()
        device = torch.device(device_id)
        model = model.to(device)

        # Apply quantization (linear layers only for dLLM)
        if quant_args is not None:
            print(f"\nApplying quantization...")
            model = quantize_linear_layers_only(model, quant_args, clip_search=clip_search)

        # Add dLLM generation method
        model.mdm_sample = types.MethodType(
            generation_functions.Fast_dLLM_QwenForCausalLM.batch_sample,
            model
        )

        # Create eval harness wrapper
        lm = FastDLLMEvalHarness(
            model=model,
            tokenizer=tokenizer,
            device=device,
            model_name=model_name,
            show_speed=show_speed,
            max_new_tokens=max_new_tokens,
            batch_size=batch_size,
            mask_id=mask_id,
            use_block_cache=False,
            small_block_size=small_block_size,
            bd_size=bd_size,
            threshold=threshold,
        )

        # Run evaluation
        print(f"\nRunning dLLM evaluation on: {tasks}")
        task_list = [tasks] if isinstance(tasks, str) else tasks
        results = evaluator.simple_evaluate(
            model=lm,
            tasks=task_list,
            num_fewshot=num_fewshot,
            batch_size=batch_size,
            apply_chat_template=True,
        )

    # === AR path (original llama_eval logic) ===
    else:
        tokenizer, model = setup_model(
            model_name, model_parallel, dtype=torch.float16,
            device=device_id if not model_parallel else None
        )
        model.eval()

        if preset != "original" and quant_args is not None:
            if use_gptq:
                logger.info(f"Getting loaders")
                trainloader = get_loaders(
                    "wikitext2", nsamples=128,
                    seed=0, model=model_name,
                    seqlen=seqlen, eval_mode=False
                )
                logger.info(f"Loaders got")

                if clip_search:
                    if clip_search_y:
                        checkpoint_dir = f"{save_dir}/ckpts_y_search/{model_name.replace('/', '_')}"
                    else:
                        checkpoint_dir = f"{save_dir}/ckpts_w_search/{model_name.replace('/', '_')}"
                else:
                    checkpoint_dir = f"{save_dir}/ckpts_no_search/{model_name.replace('/', '_')}"

                logger.info(f"Quantizing GPTQ")
                start_time = time.time()
                quantize_model_gptq(
                    model=model, dataloader=trainloader, quant_args=quant_args,
                    clip_search=clip_search, dev=device_id, save_q_model=True,
                    cali_batch_size=cali_batch_size, checkpoint_dir=checkpoint_dir,
                    resume_from_checkpoint=resume_from_checkpoint
                )
                logger.info(f"GPTQ quantized in {time.time() - start_time:.2f}s")

                if model_parallel:
                    model = move_to_gpu(model, model_parallel)
                else:
                    model.to(device_id)

                quantize_model(
                    model=model, quant_args=quant_args, linear_quantized=True,
                    full_system_sim=False, online_rotate=online_rotate,
                    clip_search=clip_search, layer_for_online_rotate=layer_for_online_rotate
                )
            else:
                # Direct cast without GPTQ
                if model_parallel:
                    model = move_to_gpu(model, model_parallel)
                else:
                    model.to(device_id)

                quantize_model(
                    model=model, quant_args=quant_args, linear_quantized=False,
                    online_rotate=online_rotate, clip_search=clip_search,
                    layer_for_online_rotate=layer_for_online_rotate
                )

        if enable_eval_harness:
            results = evaluate_with_lm_eval(
                model=model,
                tokenizer=tokenizer,
                tasks=tasks,
                max_length=seqlen,
                batch_size="auto",
                log_samples=False
            )
        else:
            results = evaluate_perplexity(
                model=model,
                tokenizer=tokenizer,
                dataset_name=tasks,
                max_length=seqlen,
                verbose=True
            )

    # Print results
    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    if 'results' in results:
        for task_name, task_results in results.get('results', {}).items():
            print(f"\n{task_name}:")
            for metric, value in task_results.items():
                if isinstance(value, (int, float)):
                    print(f"  {metric}: {value:.4f}")
    else:
        for k, v in results.items():
            print(f"  {k}: {v}")

    if log_dir:
        save_results(log_dir, results)

    return results


# Keep backward compatibility alias
llama_eval = acc_sim_eval


if __name__ == "__main__":
    from jsonargparse import CLI

    start_time = time.time()
    CLI(acc_sim_eval)
    total_time = time.time() - start_time
    print(f"\n[INFO] Total workload time: {total_time:.2f} seconds")
