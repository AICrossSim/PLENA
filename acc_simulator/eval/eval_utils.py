
import json
from datetime import datetime
from zoneinfo import ZoneInfo 
from pathlib import Path
import re
import matplotlib.pyplot as plt

import torch
from torch import nn

from transformers.models.llama.modeling_llama import (
    LlamaAttention,
    LlamaRMSNorm,
    LlamaMLP
)

from transformers import AutoModelForCausalLM, AutoTokenizer
from accelerate import dispatch_model

from safetensors.torch import save_file, load_file, save_model

from ..quantize.quantized_layers import MXFPLinearPTQ, MXFPEmbeddingPTQ, FPRMSNormPTQ
from ..models.llama_quantized import LlamaAttentionMXFP, LlamaMLPActFP
from ..quantize.quantizer.mxfp import MXFPMeta
from ..quantize.quantizer.minifloat import MinifloatMeta
from ..quantize.quantizer.mxint import MXIntMeta
from ..utils import replace_modules, create_device_map

def create_experiment_log_dir(base_dir: str = "logs") -> Path:
    # Always store logs inside acc_simulator/logs regardless of current working directory
    root_dir = Path(__file__).resolve().parent.parent 
    log_root = root_dir / base_dir 
    timestamp = datetime.now(ZoneInfo("Europe/London")).strftime("%Y%m%d-%H%M%S")
    log_dir = log_root / f"run-{timestamp}"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create symlink to latest
    latest_link = log_root / "latest"
    if latest_link.is_symlink() or latest_link.exists():
        latest_link.unlink()
    latest_link.symlink_to(log_dir, target_is_directory=True)

    return log_dir


def save_args(log_dir: Path, args: dict):
    def make_serializable(obj):
        if isinstance(obj, (Path, torch.dtype)):
            return str(obj)
        elif hasattr(obj, "__dict__"):
            return {k: make_serializable(v) for k, v in vars(obj).items()}
        elif isinstance(obj, (list, tuple)):
            return [make_serializable(v) for v in obj]
        elif isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        else:
            try:
                json.dumps(obj)
                return obj
            except TypeError:
                return str(obj)

    serializable_args = make_serializable(args)
    with open(log_dir / "args.json", "w") as f:
        json.dump(serializable_args, f, indent=2)


def save_results(log_dir: Path, results: dict):
    def make_serializable(obj):
        if isinstance(obj, (Path,)):
            return str(obj)
        elif isinstance(obj, torch.dtype):
            return str(obj)
        elif isinstance(obj, (list, tuple)):
            return [make_serializable(x) for x in obj]
        elif isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        else:
            try:
                json.dumps(obj)
                return obj
            except TypeError:
                return str(obj)

    results = make_serializable(results)

    with open(log_dir / "results.json", "w") as f:
        json.dump(results, f, indent=2)


def print_all_layers(model: nn.Module):
    print("=== Model Layers and Devices ===")
    for name, layer in model.named_modules():
        try:
            device = next(layer.parameters()).device
        except StopIteration:
            device = "No parameters"
        print(f"{name}: {type(layer).__name__} | device: {device}")
    print("====================")


def validate_preset_format(preset: str) -> None:
    """
    Ensures that the preset string:
    - Contains exactly all 5 components (X, W, B, KV, NL)
    - Appears in fixed order
    - Each followed optionally by 'q' (e.g., X or Xq)

    Raises:
        ValueError if format is invalid.
    """
    if preset == "original":
        return

    pattern = r"^(Xq|X)(Wq|W)(Bq|B)(KVq|KV)(NLq|NL)$"
    match = re.fullmatch(pattern, preset)
    if not match:
        raise ValueError(
            f"Invalid preset format: '{preset}'. Must include X, W, B, KV, and NL "
            f"in order, each optionally suffixed with 'q'."
        )


def validate_and_sanitize_quant_args(
    preset: str,
    preset_X: str | None,
    preset_W: str | None,
    preset_Kv: str | None,
    preset_NL: str | None,
) -> tuple[str | None, str | None, str | None, str | None]:
    """
    Validate and sanitize quantization flags based on the preset string.

    Ensures that:
    - If a quantization type (e.g., Xq, Wq) is specified in the preset,
      the corresponding format must be provided.
    - If not specified in the preset, any provided format is ignored with a warning.

    Raises:
        ValueError: If a required preset and quantization format is missing or invalid.

    Returns:
        A tuple of (preset_mxfp_X, preset_mxfp_W, preset_mxfp_Kv, preset_minifloat_NL),
        with unused arguments set to None.
    """
    validate_preset_format(preset)

    def check_and_clear(flag: str, arg_value: str | None, arg_name: str) -> str | None:
        if flag in preset:
            if arg_value is None:
                raise ValueError(f"Preset includes '{flag}' but '{arg_name}' is not specified.")
            # Early input Str format validation, will rasie ValueError from ../meta.py if format invalid
            if "MXFP" in arg_value:
                _ = MXFPMeta.from_string(arg_value)
            elif "MXInt" in arg_value:
                _ = MXIntMeta.from_string(arg_value)
            elif "FP" in arg_value:
                _ = MinifloatMeta.from_string(arg_value)
            return arg_value
        else:
            if arg_value is not None:
                print(f"[Warning] '{arg_name}' is provided but '{flag}' not in preset. Ignoring it.")
            return None

    preset_X = check_and_clear("Xq", preset_X, "preset_X")
    preset_W = check_and_clear("Wq", preset_W, "preset_W")
    preset_Kv = check_and_clear("KVq", preset_Kv, "preset_Kv")
    preset_NL = check_and_clear("NLq", preset_NL, "preset_NL")

    return preset_X, preset_W, preset_Kv, preset_NL


def setup_model(model_name, model_parallel, dtype, device):
        # set tokenizer like this for now
        if "meta" in model_name:
            tokenizer = AutoTokenizer.from_pretrained(
                model_name, use_fast=False, trust_remote_code=True
            )
        else:
            tokenizer = AutoTokenizer.from_pretrained(model_name)

        model = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype=dtype, attn_implementation="eager"
        )
        # Temp, load on cpu only
        return tokenizer, model
        if model_parallel:
            device_map = create_device_map(model, "auto-balanced")
            model = dispatch_model(model, device_map=device_map)
        else: 
            if device:
                model = model.to(device)
            else:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                model = model.to(device)
        return tokenizer, model

def move_to_gpu(model, model_parallel=True):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device =="cpu":
        return model
    if model_parallel:
        device_map = create_device_map(model, "auto-balanced")
        model = dispatch_model(model, device_map=device_map)
    else:
        model = model.to(device)
    return model


def quantize_model(
    model: nn.Module,
    quant_args: dict,
    linear_quantized: bool = False,
    full_system_sim: bool = False,
    skip_lm_head: bool = True,
    online_rotate: bool = False,
):
    """
    Replaces specific modules in the model with their quantized counterparts based on preset.

    Args:
        model (nn.Module): The model to modify.
        quant_args (dict): Dictionary of kwargs for each quantized module type.
        linear_only (bool): If True, only replaces nn.Linear layers.
        skip_lm_head (bool): If True, skips quantizing the "lm_head" layer.
    """
    # Replace MLP activations (e.g., SiLU)
    replace_modules(
        model,
        target_class=LlamaMLP,
        replacement_class=LlamaMLPActFP,
        factory_fn=LlamaMLPActFP.from_mlp,
        kwargs=quant_args.get("mlp_kwargs", {}),
        label="LlamaMLP"
    )

    # Replace attention (e.g., softmax, rope, matmul)
    replace_modules(
        model,
        target_class=LlamaAttention,
        replacement_class=LlamaAttentionMXFP,
        factory_fn=LlamaAttentionMXFP.from_attention,
        kwargs=quant_args.get("attn_kwargs", {}),
        label="LlamaAttention"
    )

    if linear_quantized: 
        replace_modules(
            model,
            target_class=nn.Linear,
            replacement_class=MXFPLinearPTQ,
            factory_fn=MXFPLinearPTQ.from_linear_gptq,
            kwargs=quant_args.get("fc_kwargs", {}),
            label="MXFPLinearPTQ",
            skip_names=["lm_head"] if skip_lm_head else None,
            online_rotate=online_rotate
        )
    else:
        replace_modules(
            model,
            target_class=nn.Linear,
            replacement_class=MXFPLinearPTQ,
            factory_fn=MXFPLinearPTQ.from_linear,
            kwargs=quant_args.get("fc_kwargs", {}),
            label="MXFPLinearPTQ",
            skip_names=["lm_head"] if skip_lm_head else None,
            online_rotate=online_rotate
        )

    if not full_system_sim:
        return

    # Replace embedding layers
    replace_modules(
        model,
        target_class=nn.Embedding,
        replacement_class=MXFPEmbeddingPTQ,
        factory_fn=MXFPEmbeddingPTQ.from_embedding,
        kwargs=quant_args.get("embed_kwargs", {}),
        label="Embedding"
    )

    # Replace normalization layers
    replace_modules(
        model,
        target_class=LlamaRMSNorm,
        replacement_class=FPRMSNormPTQ,
        factory_fn=FPRMSNormPTQ.from_rmsnorm,
        kwargs=quant_args.get("rms_kwargs", {}),
        label="FPRMSNormPTQ"
    )

def save_gptq(model, out_dir: str):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    # sd = model.to("cpu").state_dict()
    # save_file(sd, f"{out_dir}/model.safetensors")
    save_model(model, f"{out_dir}/model.safetensors")

def load_gptq(model, ckpt_dir: str):
    sd = load_file(f"{ckpt_dir}/model.safetensors")
    model.load_state_dict(sd, strict=True)  # requires same arch/vocab
    model.eval()
    try: model.tie_weights()
    except Exception: pass
    return model
