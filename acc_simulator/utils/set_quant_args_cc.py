from typing import Literal, Union

from ..quantize.quantizer.mxfp.meta import MXFPMeta
from ..quantize.quantizer.minifloat.meta import MinifloatMeta
from ..quantize.quantizer.minifloat import FP8_E5M2, FP8_E4M3, FP16_E8M7, FP16_E5M10
from ..quantize.quantizer.mxfp import (
    OCP_MXFP4_E2M1,
    OCP_MXFP6_E2M3,
    OCP_MXFP6_E3M2,
    OCP_MXFP8_E4M3,
    OCP_MXFP8_E5M2,
)
import re

# 提取 m4e3 中的 4 和 3

def parse_preset_argument_argument(args):
    if args.lower().startswith('mxfp') or args.lower().startswith('fp'):
        match = re.search(r"e(\d+)m(\d+)", args.lower())
        if match:
            exp_bits = int(match.group(1)) 
            mantissa_bits = int(match.group(2)) 
        else:
            raise ValueError(f"Invalid preset argument: {args}")
        if args.lower().startswith('mxfp'):
            return MXFPMeta(
                element_exp_bits=exp_bits,
                element_frac_bits=mantissa_bits,
                block_size=32,
                scale_exp_bits=8,
            )
        else:
            return MinifloatMeta(
                element_exp_bits=exp_bits,
                element_frac_bits=mantissa_bits,
                exponent_bias=None,
            )
    else:
        raise ValueError(f"Invalid preset argument: {args}")

# PRESET_META_MAP = {
#     "MXFP8_E4M3": OCP_MXFP8_E4M3,
#     "MXFP8_E5M2": OCP_MXFP8_E5M2,
#     "MXFP6_E2M3": OCP_MXFP6_E2M3,
#     "MXFP6_E3M2": OCP_MXFP6_E3M2,
#     "MXFP4_E2M1": OCP_MXFP4_E2M1,
#     "FP8_E4M3": FP8_E4M3,
#     "FP8_E5M2": FP8_E5M2,
#     "FP16_E8M7": FP16_E8M7,
#     "FP16_E5M10": FP16_E5M10,
# }


def filter_kwargs(all_kwargs: dict, allowed_keys: list[str]) -> dict:
    return {k: v for k, v in all_kwargs.items() if k in allowed_keys}


def setup_linear_args(preset, preset_mxfp_x, preset_mxfp_w, preset_minifloat_x):
    linear_kwargs = {
        "x_mxfp_meta": None,
        "w_mxfp_meta": None,
        "b_mxfp_meta": None,
        "out_minifp_meta": None,
        "layer_type": "XWB",
    }
    if preset != "original":
        if "Xq" in preset:
            linear_kwargs["x_mxfp_meta"] = parse_preset_argument_argument(preset_mxfp_x)
        if "Wq" in preset:
            linear_kwargs["w_mxfp_meta"] = parse_preset_argument_argument(preset_mxfp_w)
        # bai and weight sharing the same datatype setup
        if "Bq" in preset:
            linear_kwargs["b_mxfp_meta"] = parse_preset_argument_argument(preset_mxfp_w)
        if "Xq" in preset:
            linear_kwargs["out_minifp_meta"] = parse_preset_argument_argument(preset_minifloat_x)
        linear_kwargs["layer_type"] = preset
    
    return linear_kwargs

def setup_embed_args(preset, preset_mxfp_w):
    # Assume embedding share the same datatype setup as linear, as lm_head points to embeds' weights
    embed_kwargs = {
        "w_mxfp_meta": None,
        "layer_type": "W",
    }
    if preset != "original":
        if "Wq" in preset:
            embed_kwargs["w_mxfp_meta"] = parse_preset_argument_argument(preset_mxfp_w)
            embed_kwargs["layer_type"] = "Wq"
    
    return embed_kwargs

def setup_norm_args(preset, preset_minifloat_NL):
    rms_kwargs = {
        "x_minifp_meta": None,
        "w_minifp_meta": None,
        "layer_type": "XW",
    }
    if preset != "original" and "NLq" in preset:
        layer_type = ""
        rms_kwargs["x_minifp_meta"] = parse_preset_argument_argument(preset_minifloat_NL)
        layer_type += "Xq"
        rms_kwargs["w_minifp_meta"] = parse_preset_argument_argument(preset_minifloat_NL)
        layer_type += "Wq"
        rms_kwargs["layer_type"] = layer_type
    
    return rms_kwargs

def setup_atten_args(preset, preset_mxfp_x, preset_mxfp_w, preset_mxfp_Kv, preset_minifloat_x, preset_minifloat_NL):
    attn_kwargs = {
        "qk_q_meta": None,
        "qk_k_meta": None,
        "av_a_meta": None,
        "av_v_meta": None,
        "rope_meta": None,
        "softmax_meta": None,
        "kv_cache_meta": None,
        "qk_func_type": "XW",
        "av_func_type": "XW",
        "rope_func_type": "X",
        "softmax_func_type": "X",
        "kv_func_type": "KV"
    }
    if preset != "original":
        qk_func_type = ""
        av_func_type = ""
        if "Xq" in preset:
            attn_kwargs["qk_q_meta"] = parse_preset_argument_argument(preset_mxfp_x)
            attn_kwargs["av_a_meta"] = parse_preset_argument_argument(preset_mxfp_x)
            attn_kwargs["qk_out_meta"] = parse_preset_argument_argument(preset_minifloat_x)
            attn_kwargs["av_out_meta"] = parse_preset_argument_argument(preset_minifloat_x)
            qk_func_type += "Xq"
            av_func_type += "Xq"
            
        if "NLq" in preset:
            attn_kwargs["rope_meta"] = parse_preset_argument_argument(preset_minifloat_NL)
            attn_kwargs["softmax_meta"] = parse_preset_argument_argument(preset_minifloat_NL)
            attn_kwargs["rope_func_type"] = "Xq"
            attn_kwargs["softmax_func_type"] = "Xq"

        if "Wq" in preset:
            attn_kwargs["qk_k_meta"] = parse_preset_argument_argument(preset_mxfp_w)
            attn_kwargs["av_v_meta"] = parse_preset_argument_argument(preset_mxfp_w)
            qk_func_type += "Wq"
            av_func_type += "Wq"

        if "KVq" in preset:
            attn_kwargs["kv_cache_meta"] = parse_preset_argument_argument(preset_mxfp_Kv)
            attn_kwargs["kv_func_type"] = "KVq"

    return attn_kwargs

def setup_mlp_args(preset, preset_minifloat_NL):
    mlp_kwargs = {
        "silu_meta": None,
        "silu_func_type": "X"
    }
    if preset != "original" and "NLq" in preset:
        mlp_kwargs["silu_meta"] = parse_preset_argument_argument(preset_minifloat_NL)
        mlp_kwargs["silu_func_type"] = "Xq"
    
    return mlp_kwargs

def setup_args_linear_nonlinear_cc(
    preset: str,
    preset_mxfp_X: str | None,
    preset_mxfp_W: str | None,
    preset_mxfp_Kv: str | None,
    preset_minifloat_x: str | None,
    preset_minifloat_NL: str | None,
) -> dict:
    kwargs = {
        "preset": preset,
        "preset_mxfp_x": preset_mxfp_X,
        "preset_mxfp_w": preset_mxfp_W,
        "preset_mxfp_Kv": preset_mxfp_Kv,
        "preset_minifloat_x": preset_minifloat_x,
        "preset_minifloat_NL": preset_minifloat_NL,
    }
    
    return {
        "fc_kwargs": setup_linear_args(**filter_kwargs(kwargs, ["preset", "preset_mxfp_x", "preset_mxfp_w", "preset_minifloat_x"])),
        "embed_kwargs": setup_embed_args(**filter_kwargs(kwargs, ["preset", "preset_mxfp_w"])),
        "attn_kwargs": setup_atten_args(**filter_kwargs(kwargs, ["preset", "preset_mxfp_x", "preset_mxfp_w", "preset_mxfp_Kv", "preset_minifloat_x", "preset_minifloat_NL"])),
        "mlp_kwargs": setup_mlp_args(**filter_kwargs(kwargs, ["preset", "preset_minifloat_NL"])),
        "rms_kwargs": setup_norm_args(**filter_kwargs(kwargs, ["preset", "preset_minifloat_NL"])),
    }
