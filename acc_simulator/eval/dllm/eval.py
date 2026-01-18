# Copyright 2025 NVIDIA CORPORATION & AFFILIATES
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0
# Modified from LLaDA repos: https://github.com/ML-GSAI/LLaDA

'''
This file is inspired by the code from https://github.com/ML-GSAI/SMDM
'''
import accelerate
import torch
import re
from pathlib import Path
import random
import numpy as np
import torch.nn.functional as F
from datasets import Dataset
from lm_eval.__main__ import cli_evaluate
from lm_eval.api.model import LM
from lm_eval.api.registry import register_model
from tqdm import tqdm
import os
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig
import json
import time
import types
import generation_functions

def set_seed(seed):
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


@register_model("fast_dllm_v2")
class Fast_dLLM_v2EvalHarness(LM):
    def __init__(
        self,
        model_path='Efficient-Large-Model/Fast_dLLM_v2_7B',
        device="cuda",
        show_speed=False,
        max_new_tokens=2048,
        batch_size=32,
        mask_id=151665,
        use_block_cache=False,
        small_block_size=8,
        bd_size=32,
        threshold=0.9,
        **kwargs,
    ):

        super().__init__()

        accelerator = accelerate.Accelerator()
        if accelerator.num_processes > 1:
            self.accelerator = accelerator
        else:
            self.accelerator = None
        
        model_kwargs = {}
        if self.accelerator is not None:
            model_kwargs.update({'device_map': {'': f'{self.accelerator.device}'}})
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path, 
            trust_remote_code=True, 
            torch_dtype=torch.bfloat16, 
            **model_kwargs
        )
        self.model.eval()

        self.model.mdm_sample = types.MethodType(generation_functions.Fast_dLLM_QwenForCausalLM.batch_sample, self.model)

        self.device = torch.device(device)
        if self.accelerator is not None:
            self.model = self.accelerator.prepare(self.model)
            self.device = torch.device(f'{self.accelerator.device}')
            self._rank = self.accelerator.local_process_index
            self._world_size = self.accelerator.num_processes
        else: 
            self.model = self.model.to(device)
            self._rank = 0
            self._world_size = 1

        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        
        self.show_speed = show_speed
        self.max_new_tokens = max_new_tokens
        self.batch_size = int(batch_size)
        self.mask_id = mask_id
        self.model_path = model_path
        self.use_block_cache = use_block_cache
        self.small_block_size = small_block_size
        self.threshold = threshold
        self.bd_size = bd_size

    @property
    def rank(self):
        return self._rank
    
    @property
    def world_size(self):
        return self._world_size

    @property
    def tokenizer_name(self):
        return self.model_path
    
    def apply_chat_template(self, chat_history, add_generation_prompt=True):
        return self.tokenizer.apply_chat_template(chat_history, add_generation_prompt=add_generation_prompt, tokenize=False)
    
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

        batch = torch.cat([batch.to(self.device), torch.full((b, self.bd_size-batch.shape[1]%self.bd_size), self.mask_id, dtype=torch.long, device=self.device)], dim=1)
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

        loss_acc = []

        perturbed_seq = self._forward_process(seq.clone(), prompt_index)

        mask_indices = perturbed_seq == self.mask_id

        logits = self.get_logits(perturbed_seq)
        seq = torch.cat([seq.to(self.device), torch.full((seq.shape[0], self.bd_size-seq.shape[1]%self.bd_size), -100, dtype=torch.long, device=self.device)], dim=1)
        loss = F.cross_entropy(logits[mask_indices], seq[mask_indices], reduction='none')
        loss = loss.sum()
        loss_acc.append(loss.item())

        return - sum(loss_acc) / len(loss_acc)


    def loglikelihood(self, requests):
        def _tokenize(e):
            prefix, target = self._encode_pair(e["prefix"], e["target"])
            return {
                "prefix_text": e["prefix"],
                "target_text": e["target"],
                "prefix": prefix,
                "target": target,
            }

        ds = []
        ds = [{"prefix": req.args[0], "target": req.args[1]} for req in requests]
        ds = Dataset.from_list(ds)
        ds = ds.map(_tokenize)
        ds = ds.with_format("torch")
        prompt_len = [len(x["prefix"]) + len(x["target"]) for x in ds]

        assert max(prompt_len) <= 4096

        out = []
        with torch.no_grad():
            for elem in tqdm(ds, desc="Computing likelihood..."):
                prefix = elem["prefix"]
                target = elem["target"]

                ll = self.get_loglikelihood(prefix, target)
                out.append((ll, 0.0))
        torch.cuda.empty_cache()
        return out
    
    def generate_until(self, requests):
        output = [None] * len(requests)  # pre-allocate output list
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

        for _, batch in enumerate(tqdm(batched_requests, desc="Generating...")):
            batched_input_ids = []
            max_len = 0
            min_len = 1e9
            seq_len = []
            
            for orig_idx, req in batch:
                question = req.args[0]
                
                if req.task_name.startswith('minerva_math'):
                    question = question.replace("Solution:", "Please reason step by step, and put your final answer within \\boxed{{}}.")
                elif req.task_name.startswith('gsm8k'):
                    question = question.replace("Answer:", "Please reason step by step, and put your final answer within \\boxed{{}}.")
                model_inputs = self.tokenizer([question], return_tensors="pt").to(self.device)
                batched_input_ids.append(model_inputs["input_ids"])
                max_len = max(max_len, model_inputs["input_ids"].shape[1])
                min_len = min(min_len, model_inputs["input_ids"].shape[1])
                seq_len.append(model_inputs["input_ids"].shape[1])
            
            # pad batched_input_ids to the same length
            batched_input_ids = [torch.cat([input_ids, torch.full((1, max_len - input_ids.shape[1]), self.mask_id, dtype=torch.long, device=self.device)], dim=1) for input_ids in batched_input_ids]
            batched_input_ids = torch.cat(batched_input_ids, dim=0)
            batched_input_ids = batched_input_ids.to(self.device)
            
            with torch.no_grad():
                if self.accelerator is not None:
                    generated_ids = self.accelerator.unwrap_model(self.model).mdm_sample(
                        batched_input_ids,
                        tokenizer=self.tokenizer,
                        block_size=self.bd_size,
                        small_block_size=self.small_block_size,
                        max_new_tokens=self.max_new_tokens,
                        mask_id=self.mask_id,
                        min_len=min_len,
                        seq_len=torch.tensor(seq_len, device=self.device),
                        use_block_cache=self.use_block_cache,
                        threshold=self.threshold,
                    )
                else:
                    generated_ids = self.model.mdm_sample(
                        batched_input_ids,
                        tokenizer=self.tokenizer,
                        block_size=self.bd_size,
                        small_block_size=self.small_block_size,
                        max_new_tokens=self.max_new_tokens,
                        mask_id=self.mask_id,
                        min_len=min_len,
                        seq_len=torch.tensor(seq_len, device=self.device),
                        use_block_cache=self.use_block_cache,
                        threshold=self.threshold,
                    )
            
            # extract new generated tokens, and keep original index order
            for batch_pos, (orig_idx, req) in enumerate(batch):
                generated_answer = self.tokenizer.decode(
                    generated_ids[batch_pos][seq_len[batch_pos]:], 
                    skip_special_tokens=True
                )
            
                # count token number
                if self.show_speed:
                    num_tokens += (generated_ids[batch_pos][seq_len[batch_pos]:] != self.mask_id).sum()
                
                # put result in the correct original index position
                output[orig_idx] = generated_answer

                print('=' * 20)
                print('question: ', req.args[0])
                print('answer: ', generated_answer)
                print('=' * 20, end='\n\n')
            
        end_time = time.time()
        if self.show_speed:
            print(f"Total number of tokens generated: {num_tokens}")
            print(f"Total time taken: {end_time - start_time} seconds")
            print(f"Tokens per second: {num_tokens / (end_time - start_time)}")
            
        return output


if __name__ == "__main__":
    cli_evaluate()
    
