import torch
from accelerate import infer_auto_device_map

def convert_str_na_to_none(d):
    """
    Since toml does not support None, we use "NA" to represent None.
    """
    if isinstance(d, dict):
        for k, v in d.items():
            d[k] = convert_str_na_to_none(v)
    elif isinstance(d, list):
        d = [convert_str_na_to_none(v) for v in d]
    elif isinstance(d, tuple):
        d = tuple(convert_str_na_to_none(v) for v in d)
    else:
        if d == "NA":
            return None
        else:
            return d
    return d

def create_device_map(model, device_map) -> dict[str, int]:
    if device_map == "auto":
        return infer_auto_device_map(
            model,
            no_split_module_classes=model._no_split_modules,
        )
    elif device_map == "auto-balanced":
        n_devices = torch.cuda.device_count()
        assert n_devices > 0, "No CUDA devices found for model parallelism."

        max_memory = {
            i: torch.cuda.mem_get_info(i)[0] // 2
            for i in range(n_devices)
        }

        raw_map = infer_auto_device_map(
            model,
            no_split_module_classes=model._no_split_modules,
            max_memory=max_memory,
        )

        balanced_map = {}
        n_decoder_layers = model.config.num_hidden_layers
        n_layers_per_device = max(1, n_decoder_layers // n_devices)

        current_device = 0
        current_decoder_idx = 0
        for layer_name in raw_map:
            if ".layers." in layer_name:
                if (current_decoder_idx + 1) % n_layers_per_device == 0:
                    current_device += 1
                current_decoder_idx += 1
            balanced_map[layer_name] = min(current_device, n_devices - 1)

        return balanced_map
    else:
        assert isinstance(device_map, dict), "device_map must be a dict or 'auto'/'auto-balanced'."
        return device_map
