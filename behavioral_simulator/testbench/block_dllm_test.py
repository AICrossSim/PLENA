# This is an attempt at testing a blocked AR/Diffusion inference template

import torch
import types

###############################################################################
# Copied from Fast-dllm/v2/generation_functions.py
# from typing import Callable, Optional, Union
# from transformers.utils import auto_docstring, logging


# @auto_docstring
# class Fast_dLLM_QwenForCausalLM:

#     @torch.no_grad()
#     def batch_sample(
#         self,
#         input_ids,
#         tokenizer,
#         block_size,
#         max_new_tokens, 
#         small_block_size,
#         min_len,
#         seq_len,
#         mask_id=151665,
#         threshold=0.95,
#         stop_token=151645,
#         use_block_cache=False,
#         top_p=0.95,
#         temperature=0.0,
#     ):
#         num_blocks = max_new_tokens // block_size + seq_len.max().item() // block_size
#         batch_size = input_ids.shape[0]

#         if min_len > block_size:
#             output = self.forward(input_ids=input_ids[:, :(min_len // block_size * block_size)], use_cache=True, update_past_key_values=True, block_size=block_size)
#             logits, past_key_values = output.logits, output.past_key_values
#             if min_len % block_size == 0:
#                 predict_sample_idx = (seq_len == min_len)
#                 predict_logits = logits[predict_sample_idx, -1:, :]
#                 next_token = predict_logits.argmax(dim=-1)
#                 if input_ids.shape[1] <= min_len:
#                     input_ids = torch.cat([input_ids, next_token], dim=1)
#                 else:
#                     input_ids[predict_sample_idx, min_len] = next_token.squeeze(dim=-1)
#         else:
#             past_key_values = None

#         seq_block_idx = seq_len // block_size
#         finished_flag = torch.zeros((batch_size), device=self.device, dtype=torch.bool)

#         start_block_idx = min_len // block_size
#         num_small_blocks = block_size // small_block_size

#         sample_indices = torch.arange(batch_size, device=self.device)
#         finished_samples = {}
#         for block_idx in range(start_block_idx, num_blocks):
#             if finished_flag.all():
#                 break
#             if (seq_block_idx == block_idx).all():
#                 x_init = mask_id * torch.ones((input_ids.shape[0], block_size-input_ids.shape[1]%block_size), device=self.device, dtype=torch.long)
#                 x_init = torch.cat([input_ids, x_init], dim=1)
#                 input_ids = x_init
#             else:
#                 x_init = input_ids[:, :(block_idx + 1)*block_size]

#             x_init[finished_flag, -block_size:] = tokenizer.pad_token_id
#             x_t = x_init.clone()
#             step = 0
#             block_past_key_values = None
#             while True:
#                 mask_idx = (x_t[:, -block_size:] == mask_id)
#                 if mask_idx.sum() == 0:
#                     for sample_idx in range(x_t.shape[0]):
#                         if finished_flag[sample_idx] and seq_len[sample_idx] < (block_idx + 1) * block_size:
#                             stop_token_idx = (x_t[sample_idx, seq_len[sample_idx]:] == stop_token).nonzero()[0][0]
#                             x_t[sample_idx, seq_len[sample_idx]+stop_token_idx+1:] = tokenizer.pad_token_id
#                     if finished_flag.all():
#                         break
#                     output = self.forward(input_ids=x_t[:, -block_size:], use_cache=True, past_key_values=past_key_values, update_past_key_values=True, block_size=block_size)
#                     logits, past_key_values = output.logits, output.past_key_values
#                     next_token = logits[:, -1:, :].argmax(dim=-1)
#                     next_token[finished_flag] = tokenizer.pad_token_id
#                     x_t = torch.cat([x_t, next_token], dim=1)
#                     step += 1

#                     break
                
#                 for small_block_idx in range(num_small_blocks):
#                     small_block_start_idx = small_block_idx * small_block_size
#                     small_block_end_idx = small_block_start_idx + small_block_size

#                     start = -block_size + small_block_start_idx
#                     end = None if block_size == small_block_end_idx else -block_size + small_block_end_idx
#                     while True:
#                         mask_idx = (x_t[:, -block_size:] == mask_id)
#                         if mask_idx[:, start:end].sum() == 0:
#                             break
                        
#                         if use_block_cache:
#                             if block_past_key_values is None or (x_t[:, -block_size+small_block_start_idx] == mask_id).any():
#                                 output = self.forward(input_ids=x_t[:, -block_size:], use_cache=True, past_key_values=past_key_values, update_past_key_values=False, use_block_cache=True)
#                                 logits, block_past_key_values = output.logits, output.block_past_key_values
#                                 logits = torch.cat([logits[:, :1, :], logits[:, :-1, :]], dim=1)
#                                 logits = logits[:, start:end]
#                             else:
#                                 logits = self.forward(input_ids=x_t[:,start:end], use_cache=True, past_key_values=past_key_values, update_past_key_values=False, use_block_cache=True, block_past_key_values=block_past_key_values, replace_position=small_block_start_idx).logits
#                                 logits = torch.cat([logits[:, :1, :], logits[:, :-1, :]], dim=1)
#                         else:
#                             logits = self.forward(input_ids=x_t[:, -block_size:], use_cache=True, past_key_values=past_key_values, update_past_key_values=False).logits
#                             logits = torch.cat([logits[:, :1, :], logits[:, :-1, :]], dim=1)
#                             logits = logits[:, start:end]
#                         x_1, p_1t = self.sample_with_top_p(logits, top_p=top_p, temperature=temperature)
#                         x1_p = torch.squeeze(torch.gather(p_1t, dim=-1, index=torch.unsqueeze(x_1, -1)), -1)
#                         x1_p = torch.where(mask_idx[:, start:end], x1_p, -torch.inf)

#                         unmask_idx = (x1_p > threshold)
#                         max_prob_idx = x1_p.argmax(dim=-1)
#                         unmask_idx[torch.arange(x_1.shape[0]), max_prob_idx] = True
#                         unmask_idx = unmask_idx & mask_idx[:, start:end]

#                         x_t[:, start:end][unmask_idx] = x_1[unmask_idx]

#                         finished_row_flags = ((x_1 == stop_token) & unmask_idx).any(dim=1) # shape: [B]
#                         finished_flag = finished_flag | finished_row_flags

#                         step += 1

#             if input_ids.shape[1] ==  x_t.shape[1]:
#                 input_ids = x_t
#             else:
#                 input_ids[:, :(block_idx + 1)*block_size] = x_t[:, :-1]
#                 if (seq_block_idx == block_idx).all():
#                     input_ids = torch.cat([input_ids, x_t[:, -1:]], dim=1)
#                 else:
#                     if input_ids.shape[1] <= (block_idx + 1)*block_size:
#                         input_ids = x_t
#                     else:
#                         input_ids[seq_block_idx == block_idx, (block_idx + 1)*block_size] = x_t[seq_block_idx == block_idx, (block_idx + 1)*block_size]
#             seq_block_idx[seq_block_idx == block_idx] = block_idx + 1
#             if finished_flag.any():
#                 for sample_idx in range(x_t.shape[0]):
#                     if finished_flag[sample_idx]:
#                         original_idx = sample_indices[sample_idx].item()
#                         finished_samples[original_idx] = x_t[sample_idx:sample_idx+1].clone().squeeze(dim=0)
#                 sample_indices = sample_indices[~finished_flag]
#                 input_ids = input_ids[~finished_flag]
#                 seq_block_idx = seq_block_idx[~finished_flag]
#                 seq_len = seq_len[~finished_flag]
#                 x_t = x_t[~finished_flag]

#                 for layer_id in range(len(past_key_values)):
#                     past_key_values.key_cache[layer_id] = past_key_values.key_cache[layer_id][~finished_flag]
#                     past_key_values.value_cache[layer_id] = past_key_values.value_cache[layer_id][~finished_flag]

#                 finished_flag = finished_flag[~finished_flag]



#         # add not finished samples since max_new_tokens is reached
#         if len(finished_samples) < batch_size:
#             for sample_idx in range(x_t.shape[0]):
#                 original_idx = sample_indices[sample_idx].item()
#                 finished_samples[original_idx] = x_t[sample_idx:sample_idx+1].clone().squeeze(dim=0)
        
#         assert len(finished_samples) == batch_size
#         return finished_samples
###############################################################################