import logging
from copy import deepcopy

import toml

from ...utils.config_load import convert_str_na_to_none
from tools.quant.quant_config_parser import parse_node_config

logger = logging.getLogger(__name__)

"""
An example of quant_config for llama, llamaforcasualLM

{
    "embedding": {},
    "model_layer": {
        "self_attn": {
            "q_proj": {},
            "k_proj": {},
            "v_proj": {},
            "o_proj": {},
            "rotary_positional_encoding": {},
            "matmul_0": {},
            "matmul_1": {},
            "softmax": {},
        },
        "mlp": {
            "gate_proj": {},
            "down_proj": {},
            "up_proj": {},
        },
    }
    "norm": {},
    "linear_default": {},
    "matmul_default": {},
    "casual_lm_head": {},
    "silu": {},
}
"""


def create_a_layer_config(
    linear_qc: dict = None,
    matmul_qc: dict = None,
    rotary_positional_encoding_qc: dict = None,
    silu_qc: dict = None,
    softmax_qc: dict = None,
    layer_qc=None,
    strict: bool = True,
) -> dict:
    if (layer_qc is None and matmul_qc is None) and layer_qc is None:
        raise ValueError("Must provide either (linear_qc & matmul_qc) or layer_qc")
    if layer_qc is None:
        layer_qc = {}
    # fmt: off
    qc = {
        "self_attn": {
            "q_proj": deepcopy(parse_node_config(layer_qc.get("self_attn", {}).get("q_proj", linear_qc), "linear", strict=strict)),
            "k_proj": deepcopy(parse_node_config(layer_qc.get("self_attn", {}).get("k_proj", linear_qc), "linear", strict=strict)),
            "v_proj": deepcopy(parse_node_config(layer_qc.get("self_attn", {}).get("v_proj", linear_qc), "linear", strict=strict)),
            "o_proj": deepcopy(parse_node_config(layer_qc.get("self_attn", {}).get("o_proj", linear_qc), "linear", strict=strict)),
            "rotary_positional_encoding": deepcopy(parse_node_config(layer_qc.get("self_attn", {}).get("rotary_positional_encoding", rotary_positional_encoding_qc), "rotary_positional_encoding", strict=strict)),
            "matmul_0": deepcopy(parse_node_config(layer_qc.get("self_attn", {}).get("matmul_0", matmul_qc), "matmul", strict=strict)),
            "matmul_1": deepcopy(parse_node_config(layer_qc.get("self_attn", {}).get("matmul_1", matmul_qc), "matmul", strict=strict)),
            "softmax": deepcopy(parse_node_config(layer_qc.get("self_attn", {}).get("softmax", softmax_qc), "softmax", strict=strict)),
        },
        "mlp": {
            "gate_proj": deepcopy(parse_node_config(layer_qc.get("mlp", {}).get("gate_proj", linear_qc), "linear", strict=strict)),
            "down_proj": deepcopy(parse_node_config(layer_qc.get("mlp", {}).get("down_proj", linear_qc), "linear", strict=strict)),
            "up_proj": deepcopy(parse_node_config(layer_qc.get("mlp", {}).get("up_proj", linear_qc), "linear", strict=strict)),
            "silu": deepcopy(parse_node_config(layer_qc.get("mlp", {}).get("silu", silu_qc), "silu", strict=strict))
        },
    }
    # fmt: on
    return qc


def _parse_and_complete_config(
    config: dict,
    num_hidden_layers: int,
    strict: bool = True,
) -> dict:
    assert "default" in config, "Must provide default config for by_name_parser"
    default_qc: dict = config["default"]
    linear_qc: dict = parse_node_config(
        config.get("linear", default_qc), mase_op="linear"
    )
    rotary_positional_encoding_qc: dict = parse_node_config(
        config.get("rotary_positional_encoding", config["rotary_positional_encoding"]),
        mase_op="rotary_positional_encoding",
    )
    config["rotary_positional_encoding"]["bypass"] = True

    casual_lm_head_qc: dict = parse_node_config(
        config.get("casual_lm_head",  config["casual_lm_head"]),
        mase_op="linear",
    )
    input_embedding_qc: dict = parse_node_config(
        config.get("embedding", config["embedding"]),
        mase_op="embedding",
    )
    rms_norm_qc: dict = parse_node_config(
        config.get("rms_norm", config["rms_norm"]),
        mase_op="rms_norm",
    )
    matmul_qc: dict = parse_node_config(
        config.get("matmul", default_qc), mase_op="matmul"
    )
    silu_qc: dict = parse_node_config(
        config.get("silu", config["silu"]), mase_op="silu"
    )
    softmax_qc: dict = parse_node_config(
        config.get("softmax", config["softmax"]), mase_op="softmax"
    )
    general_layer_qc: dict = config.get("model_layer", None)

    # parsed config
    p_config = {}
    for i in range(num_hidden_layers):
        layer_entry = f"model_layer_{i}"
        layer_qc = config.get(layer_entry, general_layer_qc)
        p_config[layer_entry] = create_a_layer_config(
            linear_qc, matmul_qc, rotary_positional_encoding_qc, silu_qc, softmax_qc, layer_qc, strict=strict
        )
    p_config["default"] = default_qc
    p_config["casual_lm_head"] = casual_lm_head_qc
    p_config["embedding"] = input_embedding_qc
    p_config["rms_norm"] = rms_norm_qc
    return p_config


def parse_llama_quantized_config(
    config: str | dict | None, num_hidden_layers: int, strict: bool = True
) -> dict:
    assert isinstance(
        config, (str, dict, type(None))
    ), "config must be a str path to config toml, None or dict"

    if config is None:
        return None

    if isinstance(config, str):
        config = toml.load(config)

    config = convert_str_na_to_none(config)
    parsed_config = _parse_and_complete_config(config, num_hidden_layers, strict=strict)
    return parsed_config
