import torch
from typing import Literal
from accelerate import infer_auto_device_map

def create_device_map(
    model: torch.nn.Module,
    device_map: dict[str, int] | Literal["auto", "auto-balanced"],
) -> dict[str, int]:
    if device_map == "auto":
        device_map = infer_auto_device_map(
            model, no_split_module_classes=model._no_split_modules
        )
    elif device_map == "auto-balanced":
        max_memory = {
            i: torch.cuda.mem_get_info(i)[0] // 4
            for i in range(torch.cuda.device_count())
        }
        device_map = infer_auto_device_map(
            model,
            no_split_module_classes=model._no_split_modules,
            max_memory=max_memory,
        )
        n_devices = torch.cuda.device_count()
        n_decoder_layers = model.config.num_hidden_layers
        n_layers_per_device = n_decoder_layers // n_devices
        balanced_device_map = {}
        current_device = 0
        current_decoder_idx = 0

        for layer_name in device_map:
            if ".layers." in layer_name:
                if (current_decoder_idx + 1) % n_layers_per_device == 0:
                    current_device += 1
                current_decoder_idx += 1
            balanced_device_map[layer_name] = min(current_device, n_devices - 1)
        device_map = balanced_device_map
    else:
        assert isinstance(device_map, dict)
    return device_map