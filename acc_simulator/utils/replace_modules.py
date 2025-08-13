import gc
import time
from typing import Optional, Callable

import torch
from torch import nn

from transformers.models.llama.modeling_llama import LlamaForCausalLM


def get_layer_by_name(model: nn.Module, name: str) -> nn.Module:
    parts = name.split(".")
    module = model
    for part in parts:
        if part.isdigit():
            module = module[int(part)]
        else:
            module = getattr(module, part)
    return module


def set_layer_by_name(module: torch.nn.Module, name: str, new_layer: torch.nn.Module) -> None:
    levels = name.split(".")
    if len(levels) > 1:
        mod_ = module
        for l_idx in range(len(levels) - 1):
            if levels[l_idx].isdigit():
                mod_ = mod_[int(levels[l_idx])]
            else:
                mod_ = getattr(mod_, levels[l_idx])
        setattr(mod_, levels[-1], new_layer)
    else:
        setattr(module, name, new_layer)


def replace_modules(
    model: nn.Module,
    target_class: type,
    replacement_class: type,
    factory_fn: Callable[..., nn.Module],
    kwargs: dict,
    skip_names: Optional[list[str]] = None,
    label: str = "layer"
) -> nn.Module:
    assert isinstance(model, LlamaForCausalLM)
    replaced = 0
    t_start = time.time()

    layer_names = [
        name for name, layer in model.named_modules()
        if isinstance(layer, target_class)
    ]

    for name in layer_names:
        old_layer = get_layer_by_name(model, name)

        if isinstance(old_layer, replacement_class):
            print(f"Skipping already replaced {label}: {name}")
            continue
        if skip_names and name in skip_names:
            print(f"Skipping {label}: {name}")
            continue
        
        # Only rotate activation in down-projection
        if target_class == nn.Linear and "down_proj" not in name and kwargs["online_rotate"] == True:
            kwargs["online_rotate"] = False

        new_layer = factory_fn(old_layer, **kwargs)
        set_layer_by_name(model, name, new_layer)

        # Safely delete old layer if on GPU
        param = next(old_layer.parameters(), None)
        if param is not None and param.device.type == "cuda":
            del old_layer
            gc.collect()
            torch.cuda.empty_cache()

        replaced += 1

    print(f"Replaced {replaced} {label}(s) in {time.time() - t_start:.2f}s")
    return model