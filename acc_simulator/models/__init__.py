from .llama_quantized import LlamaQuantizedConfig, LlamaQuantizedForCausalLM

MODEL_MAP = {
    "llama": {
        # lm-language modeling
        "lm": LlamaQuantizedForCausalLM
    }
}

CONFIG_MAP = {
    "llama": LlamaQuantizedConfig
}


def get_model_cls(arch: str, task: str):
    assert arch in MODEL_MAP, f"arch {arch} not supported"
    assert task in MODEL_MAP[arch], f"task {task} not supported for arch {arch}"
    return MODEL_MAP[arch][task]

def get_config_cls(arch: str):
    assert arch in CONFIG_MAP, f"arch {arch} not supported"
    return CONFIG_MAP[arch]