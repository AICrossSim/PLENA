"""
Fast-dLLM evaluation with optional MXInt quantization.

Usage:
    python -m acc_simulator.cli.dllm_sim --help

Example (baseline):
    python -m acc_simulator.cli.dllm_sim \
        --model_name Efficient-Large-Model/Fast_dLLM_v2_1.5B \
        --tasks gsm8k

Example (with quantization):
    python -m acc_simulator.cli.dllm_sim \
        --model_name Efficient-Large-Model/Fast_dLLM_v2_1.5B \
        --tasks gsm8k \
        --preset XWqB \
        --preset_W MXINT_4_B32_S8
"""

import time
import types
from typing import Union
import torch
from torch import nn

from transformers import AutoModelForCausalLM, AutoTokenizer
from lm_eval import evaluator
from lm_eval.api.model import LM
from tqdm import tqdm
from datasets import Dataset
import torch.nn.functional as F

from acc_simulator.quantize.quantized_layers.linear import MXFPLinearPTQ
from acc_simulator.utils.set_quant_args import setup_linear_args
from acc_simulator.eval.dllm import generation_functions


def quantize_linear_layers(
    model: nn.Module,
    preset: str,
    preset_W: str,
    skip_lm_head: bool = True,
):
    """
    Replace nn.Linear layers with MXFPLinearPTQ based on preset.

    Args:
        model: The model to quantize
        preset: Layer type pattern (e.g., "XWqB" for weight-only quantization)
        preset_W: Weight quantization format (e.g., "MXINT_4_B32_S8")
        skip_lm_head: Whether to skip the lm_head layer
    """
    fc_kwargs = setup_linear_args(
        preset=preset,
        preset_x=preset_W,
        preset_w=preset_W,
        preset_NL=None,
        online_rotate=False,
        clip_search_y=False
    )

    linear_count = sum(1 for _, m in model.named_modules() if isinstance(m, nn.Linear))
    print(f"Found {linear_count} nn.Linear layers")
    print(f"Preset: {preset}, Format: {preset_W}")

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


class FastDLLMEvalHarness(LM):
    """
    lm-eval harness wrapper for Fast-dLLM v2.
    Based on the original Fast-dLLM v2 eval.py implementation.
    """

    def __init__(
        self,
        model,
        tokenizer,
        device,
        model_name: str,
        show_speed: bool = False,
        max_new_tokens: int = 2048,
        batch_size: int = 32,
        mask_id: int = 151665,
        use_block_cache: bool = False,
        small_block_size: int = 8,
        bd_size: int = 32,
        threshold: float = 0.9,
    ):
        super().__init__()

        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.model_name = model_name
        self.show_speed = show_speed
        self.max_new_tokens = max_new_tokens
        self.batch_size = batch_size
        self.mask_id = mask_id
        self.use_block_cache = use_block_cache
        self.small_block_size = small_block_size
        self.bd_size = bd_size
        self.threshold = threshold

        self._rank = 0
        self._world_size = 1

    @property
    def rank(self):
        return self._rank

    @property
    def world_size(self):
        return self._world_size

    @property
    def tokenizer_name(self):
        return self.model_name

    def apply_chat_template(self, chat_history, add_generation_prompt=True):
        return self.tokenizer.apply_chat_template(
            chat_history, add_generation_prompt=add_generation_prompt, tokenize=False
        )

    def loglikelihood_rolling(self, requests):
        raise NotImplementedError

    def _encode_pair(self, context, continuation):
        whole_enc = self.tokenizer(context + continuation)["input_ids"]
        context_enc = self.tokenizer(context)["input_ids"]
        context_enc_len = len(context_enc)
        continuation_enc = whole_enc[context_enc_len:]
        return context_enc, continuation_enc

    def _forward_process(self, batch, prompt_index):
        b, l = batch.shape
        batch[:, prompt_index.sum()] = self.mask_id
        batch = torch.cat([
            batch.to(self.device),
            torch.full((b, self.bd_size - batch.shape[1] % self.bd_size),
                      self.mask_id, dtype=torch.long, device=self.device)
        ], dim=1)
        if batch.shape[1] > l:
            batch[:, l] = self.tokenizer.eos_token_id
        return batch

    @torch.no_grad()
    def get_logits(self, batch):
        logits = self.model(batch).logits
        logits = torch.cat([logits[:, :1, :], logits[:, :-1, :]], dim=1)
        return logits[:, :batch.shape[1]]

    @torch.no_grad()
    def get_loglikelihood(self, prefix, target):
        seq = torch.concatenate([prefix, target])[None, :]
        prompt_index = torch.arange(seq.shape[1], device=self.device) < len(prefix)
        perturbed_seq = self._forward_process(seq.clone(), prompt_index)
        mask_indices = perturbed_seq == self.mask_id
        logits = self.get_logits(perturbed_seq)
        seq = torch.cat([
            seq.to(self.device),
            torch.full((seq.shape[0], self.bd_size - seq.shape[1] % self.bd_size),
                      -100, dtype=torch.long, device=self.device)
        ], dim=1)
        loss = F.cross_entropy(logits[mask_indices], seq[mask_indices], reduction='none')
        return -loss.sum().item()

    def loglikelihood(self, requests):
        def _tokenize(e):
            prefix, target = self._encode_pair(e["prefix"], e["target"])
            return {"prefix": prefix, "target": target}

        ds = [{"prefix": req.args[0], "target": req.args[1]} for req in requests]
        ds = Dataset.from_list(ds)
        ds = ds.map(_tokenize)
        ds = ds.with_format("torch")

        out = []
        with torch.no_grad():
            for elem in tqdm(ds, desc="Computing likelihood..."):
                ll = self.get_loglikelihood(elem["prefix"], elem["target"])
                out.append((ll, 0.0))
        torch.cuda.empty_cache()
        return out

    def generate_until(self, requests):
        output = [None] * len(requests)
        num_tokens = 0
        start_time = time.time()

        requests_with_indices = [(i, req) for i, req in enumerate(requests)]
        requests_with_indices.sort(key=lambda x: len(x[1].args[0]))

        batched_requests = []
        current_batch = []
        for i, req in requests_with_indices:
            current_batch.append((i, req))
            if len(current_batch) == self.batch_size:
                batched_requests.append(current_batch)
                current_batch = []
        if current_batch:
            batched_requests.append(current_batch)

        for batch in tqdm(batched_requests, desc="Generating..."):
            batched_input_ids = []
            max_len = 0
            min_len = 1e9
            seq_len = []

            for orig_idx, req in batch:
                question = req.args[0]

                # Prompt formatting for math tasks (matching original Fast-dLLM)
                if req.task_name.startswith('minerva_math'):
                    question = question.replace("Solution:", "Please reason step by step, and put your final answer within \\boxed{{}}.")
                elif req.task_name.startswith('gsm8k'):
                    question = question.replace("Answer:", "Please reason step by step, and put your final answer within \\boxed{{}}.")

                model_inputs = self.tokenizer([question], return_tensors="pt").to(self.device)
                batched_input_ids.append(model_inputs["input_ids"])
                max_len = max(max_len, model_inputs["input_ids"].shape[1])
                min_len = min(min_len, model_inputs["input_ids"].shape[1])
                seq_len.append(model_inputs["input_ids"].shape[1])

            batched_input_ids = [
                torch.cat([
                    input_ids,
                    torch.full((1, max_len - input_ids.shape[1]),
                              self.mask_id, dtype=torch.long, device=self.device)
                ], dim=1)
                for input_ids in batched_input_ids
            ]
            batched_input_ids = torch.cat(batched_input_ids, dim=0)

            with torch.no_grad():
                generated_ids = self.model.mdm_sample(
                    batched_input_ids,
                    tokenizer=self.tokenizer,
                    block_size=self.bd_size,
                    small_block_size=self.small_block_size,
                    max_new_tokens=self.max_new_tokens,
                    mask_id=self.mask_id,
                    min_len=int(min_len),
                    seq_len=torch.tensor(seq_len, device=self.device),
                    use_block_cache=self.use_block_cache,
                    threshold=self.threshold,
                )

            for batch_pos, (orig_idx, req) in enumerate(batch):
                generated_answer = self.tokenizer.decode(
                    generated_ids[batch_pos][seq_len[batch_pos]:],
                    skip_special_tokens=True
                )

                if self.show_speed:
                    num_tokens += (generated_ids[batch_pos][seq_len[batch_pos]:] != self.mask_id).sum()

                output[orig_idx] = generated_answer

                print('=' * 20)
                print('question: ', req.args[0][:200])
                print('answer: ', generated_answer[:200])
                print('=' * 20, end='\n\n')

        if self.show_speed:
            elapsed = time.time() - start_time
            print(f"Total tokens: {num_tokens}, Time: {elapsed:.2f}s, Tokens/s: {num_tokens / elapsed:.2f}")

        return output


def dllm_eval(
    model_name: str = "Efficient-Large-Model/Fast_dLLM_v2_1.5B",
    tasks: Union[str, list[str]] = "gsm8k",
    device_id: str = "cuda:0",
    batch_size: int = 32,
    max_new_tokens: int = 2048,
    num_fewshot: int = 0,
    # dLLM specific
    mask_id: int = 151665,
    bd_size: int = 32,
    small_block_size: int = 8,
    threshold: float = 1.0,
    show_speed: bool = True,
    # Quantization (optional)
    preset: Union[str, None] = None,
    preset_W: Union[str, None] = None,
):
    """
    Evaluate Fast-dLLM v2 model with optional quantization.

    Args:
        model_name: HuggingFace model path
        tasks: lm-eval task(s) to run
        device_id: CUDA device
        batch_size: Batch size for evaluation
        max_new_tokens: Max tokens to generate
        num_fewshot: Number of few-shot examples
        mask_id: Mask token ID for dLLM
        bd_size: Block diffusion size
        small_block_size: Sub-block size
        threshold: Unmasking threshold
        show_speed: Show throughput metrics
        preset: Quantization layer type (e.g., "XWqB")
        preset_W: Quantization format (e.g., "MXINT_4_B32_S8")
    """
    print("=" * 60)
    print("Fast-dLLM Evaluation")
    print("=" * 60)
    print(f"Model: {model_name}")
    print(f"Tasks: {tasks}")
    print(f"Quantization: {preset} / {preset_W}" if preset else "None (BF16)")
    print("=" * 60)

    # Load model
    print(f"\nLoading model from {model_name}...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

    model.eval()
    device = torch.device(device_id)
    model = model.to(device)

    # Apply quantization if specified (must be after moving to device)
    if preset is not None and preset_W is not None:
        print(f"\nApplying quantization: {preset} with {preset_W}")
        model = quantize_linear_layers(model, preset, preset_W)

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
    print(f"\nRunning evaluation on: {tasks}")
    task_list = [tasks] if isinstance(tasks, str) else tasks
    results = evaluator.simple_evaluate(
        model=lm,
        tasks=task_list,
        num_fewshot=num_fewshot,
        batch_size=batch_size,
        apply_chat_template=True,
    )

    # Print results
    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    for task_name, task_results in results.get('results', {}).items():
        print(f"\n{task_name}:")
        for metric, value in task_results.items():
            if isinstance(value, (int, float)):
                print(f"  {metric}: {value:.4f}")

    return results


if __name__ == "__main__":
    from jsonargparse import CLI
    start_time = time.time()
    CLI(dllm_eval)
    print(f"\n[INFO] Total time: {time.time() - start_time:.2f}s")
