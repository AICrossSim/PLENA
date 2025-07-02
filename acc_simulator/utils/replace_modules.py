from typing import Optional
import time

import gc
import torch
from torch import nn
from mase_triton.utils.torch_module import set_layer_by_name

from transformers.models.llama.modeling_llama import LlamaForCausalLM


def replace_modules(
    model: nn.Module,
    target_class: type,
    replacement_class: type,
    factory_fn: callable,
    kwargs: dict,
    skip_names: Optional[list[str]] = None,
    label: str = "layer"
) -> nn.Module:
    assert isinstance(model, LlamaForCausalLM)
    replaced = 0
    t_start = time.time()
 
    for name, layer in model.named_modules():
        if not isinstance(layer, target_class):
            continue
        if isinstance(layer, replacement_class):
            print(f"Skipping already replaced {label}: {name}")
            continue
        if skip_names and name in skip_names:
            print(f"Skipping {label}: {name}")
            continue

        t_layer = time.time()
        new_layer = factory_fn(layer, **kwargs)
        set_layer_by_name(model, name, new_layer)

        # Free memory
        if any(p.device.type == "cuda" for p in layer.parameters()):
            del layer
            torch.cuda.empty_cache()
            gc.collect()

        t_elapsed = time.time() - t_layer
        print(f"Replaced {label}: {name} in {t_elapsed:.2f}s")
        replaced += 1

    print(f"Replaced {replaced} {label}(s) in {time.time() - t_start:.2f}s")
    return model


