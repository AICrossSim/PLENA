"""Tool for loading workload/model configurations."""

from typing import Dict, Any, Optional
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_LIB_PATH = PROJECT_ROOT / "doc" / "Model_Lib"


def get_workload(
    model_name: str,
    layer_type: str = "ffn",
    batch_size: int = 1,
    seq_len: int = 1,
) -> Dict[str, Any]:
    """
    Get workload dimensions for a specific model and layer type.

    Args:
        model_name: Model name (e.g., 'llama-3.2-1b', 'llama-3.1-8b')
        layer_type: Layer type ('ffn', 'attention', 'projection', 'rms_norm')
        batch_size: Batch size for the workload
        seq_len: Sequence length for the workload

    Returns:
        Dict with layer-specific dimensions and hardware config
    """
    # Load model config
    config_path = MODEL_LIB_PATH / f"{model_name}.json"
    if not config_path.exists():
        available = [f.stem for f in MODEL_LIB_PATH.glob("*.json")]
        return {
            "error": f"Model '{model_name}' not found. Available: {available}"
        }

    with open(config_path) as f:
        model_config = json.load(f)

    # Extract common dimensions
    hidden_size = model_config.get("hidden_size")
    intermediate_size = model_config.get("intermediate_size")
    num_attention_heads = model_config.get("num_attention_heads")
    num_kv_heads = model_config.get("num_key_value_heads")
    head_dim = model_config.get("head_dim", hidden_size // num_attention_heads)

    # Load hardware config
    hw_config = _get_hw_config()

    # Build layer-specific workload
    workload = {
        "model_name": model_name,
        "layer_type": layer_type,
        "batch_size": batch_size,
        "seq_len": seq_len,
        "hw_config": hw_config,
    }

    if layer_type == "ffn":
        workload.update({
            "hidden_size": hidden_size,
            "intermediate_size": intermediate_size,
            "activation": model_config.get("hidden_act", "silu"),
            # Matrix dimensions for assembly
            "up_weight_shape": [hidden_size, intermediate_size],
            "gate_weight_shape": [hidden_size, intermediate_size],
            "down_weight_shape": [intermediate_size, hidden_size],
            "input_shape": [batch_size * seq_len, hidden_size],
            "fp_sram_layout": {
                0: "0.0 (for negation: 0 - x = -x)",
                1: "1e-6 (epsilon)",
                2: "1.0 (for sigmoid: 1 + exp(-x))",
            },
        })

    elif layer_type == "attention":
        workload.update({
            "hidden_size": hidden_size,
            "num_attention_heads": num_attention_heads,
            "num_kv_heads": num_kv_heads,
            "head_dim": head_dim,
            # Matrix dimensions
            "q_proj_shape": [hidden_size, num_attention_heads * head_dim],
            "k_proj_shape": [hidden_size, num_kv_heads * head_dim],
            "v_proj_shape": [hidden_size, num_kv_heads * head_dim],
            "o_proj_shape": [num_attention_heads * head_dim, hidden_size],
        })

    elif layer_type == "projection":
        workload.update({
            "hidden_size": hidden_size,
            "input_shape": [batch_size * seq_len, hidden_size],
            "weight_shape": [hidden_size, hidden_size],
        })

    elif layer_type == "rms_norm":
        eps = model_config.get("rms_norm_eps", 1e-5)
        workload.update({
            "hidden_size": hidden_size,
            "eps": eps,
            "input_shape": [batch_size * seq_len, hidden_size],
            "fp_sram_layout": {
                0: "0.0 (unused)",
                1: f"epsilon = {eps}",
                2: f"1/hidden_size = {1.0 / hidden_size}",
            },
        })

    elif layer_type == "silu":
        workload.update({
            "hidden_size": hidden_size,
            "input_shape": [batch_size * seq_len, hidden_size],
            "fp_sram_layout": {
                0: "0.0 (for negation: 0 - x = -x)",
                1: "1.0 (for sigmoid: 1 + exp(-x))",
            },
        })

    return workload


def _get_hw_config() -> Dict[str, int]:
    """Load hardware config (MLEN, VLEN, BLEN)."""
    # TODO: Load from configuration.svh
    # For now return defaults
    #
    # from utils.load_config import load_svh_settings
    # cfg_path = PROJECT_ROOT / "src" / "definitions" / "configuration.svh"
    # settings = load_svh_settings(str(cfg_path))
    # return {
    #     "mlen": settings.get("MLEN", 64),
    #     "vlen": settings.get("VLEN", 64),
    #     "blen": settings.get("BLEN", 4),
    # }

    return {
        "mlen": 64,
        "vlen": 64,
        "blen": 4,
    }


def list_available_models() -> list:
    """List available model configs."""
    return [f.stem for f in MODEL_LIB_PATH.glob("*.json")]
