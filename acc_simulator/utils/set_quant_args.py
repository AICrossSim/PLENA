from ..quantize.quantizer.minifloat import MinifloatMeta
from ..quantize.quantizer.mxfp import MXFPMeta
from ..quantize.quantizer.mxint import MXIntMeta


def filter_kwargs(all_kwargs: dict, allowed_keys: list[str]) -> dict:
    return {k: v for k, v in all_kwargs.items() if k in allowed_keys}

def get_preset_info(preset):
    if "MXINT" in preset:
        return MXIntMeta.from_string(preset)
    elif "MXFP" in preset:
        return MXFPMeta.from_string(preset)
    elif "MINIFLOAT" in preset:
        return MinifloatMeta.from_string(preset)
    else:
        raise Warning(f"None preset: {preset}")

def setup_linear_args(preset, preset_x, preset_w, preset_NL, online_rotate, clip_search_y):
    linear_kwargs = {
        "x_meta": None,
        "w_meta": None,
        "b_meta": None,
        "nl_meta": None,
        "layer_type": "XWB",
        "online_rotate": online_rotate,
        "clip_search_y": clip_search_y,
    }
    if preset != "original":
        if "Xq" in preset:
            linear_kwargs["x_meta"] = get_preset_info(preset_x)
        if "Wq" in preset:
            linear_kwargs["w_meta"] = get_preset_info(preset_w)
        # bias and weights sharing the same datatype setup
        if "Bq" in preset:
            linear_kwargs["b_meta"] = get_preset_info(preset_w)
        if "NLq" in preset:
            linear_kwargs["nl_meta"] = get_preset_info(preset_NL)
        linear_kwargs["layer_type"] = preset
    
    return linear_kwargs

def setup_embed_args(preset, preset_w):
    # Assume embedding share the same datatype setup as linear, as lm_head points to embeds' weights
    embed_kwargs = {
        "w_meta": None,
        "layer_type": "W",
    }
    if preset != "original":
        if "Wq" in preset:
            embed_kwargs["w_meta"] = get_preset_info(preset_w)
            embed_kwargs["layer_type"] = "Wq"
    
    return embed_kwargs

def setup_norm_args(preset, preset_NL):
    rms_kwargs = {
        "x_meta": None,
        "w_meta": None,
        "layer_type": "XW",
    }
    if preset != "original" and "NLq" in preset:
        layer_type = ""
        rms_kwargs["x_meta"] = get_preset_info(preset_NL)
        layer_type += "Xq"
        rms_kwargs["w_meta"] = get_preset_info(preset_NL)
        layer_type += "Wq"
        rms_kwargs["layer_type"] = layer_type
    
    return rms_kwargs

def setup_atten_args(preset, preset_x, preset_w, preset_Kv, preset_NL, online_rotate):
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
        "kv_func_type": "KV",
        "online_rotate": online_rotate
    }
    if preset != "original":
        qk_func_type = ""
        av_func_type = ""
        if "Xq" in preset:
            attn_kwargs["qk_q_meta"] = get_preset_info(preset_x)
            attn_kwargs["av_a_meta"] = get_preset_info(preset_x)
            qk_func_type += "Xq"
            av_func_type += "Xq"
            
        if "NLq" in preset:
            attn_kwargs["rope_meta"] = get_preset_info(preset_NL)
            attn_kwargs["softmax_meta"] = get_preset_info(preset_NL)
            attn_kwargs["rope_func_type"] = "Xq"
            attn_kwargs["softmax_func_type"] = "Xq"

        if "Wq" in preset:
            attn_kwargs["qk_k_meta"] = get_preset_info(preset_w)
            attn_kwargs["av_v_meta"] = get_preset_info(preset_w)
            qk_func_type += "Wq"
            av_func_type += "Wq"

        if "KVq" in preset:
            attn_kwargs["kv_cache_meta"] = get_preset_info(preset_Kv)
            attn_kwargs["kv_func_type"] = "KVq"

    return attn_kwargs

def setup_mlp_args(preset, preset_NL):
    mlp_kwargs = {
        "silu_meta": None,
        "silu_func_type": "X"
    }
    if preset != "original" and "NLq" in preset:
        mlp_kwargs["silu_meta"] = get_preset_info(preset_NL)
        mlp_kwargs["silu_func_type"] = "Xq"
    
    return mlp_kwargs

def setup_args_linear_nonlinear(
    preset: str,
    preset_X: str | None,
    preset_W: str | None,
    preset_Kv: str | None,
    preset_NL: str | None,
    online_rotate: bool,
    clip_search_y : bool
) -> dict:
    kwargs = {
        "preset": preset,
        "preset_x": preset_X,
        "preset_w": preset_W,
        "preset_Kv": preset_Kv,
        "preset_NL": preset_NL,
        "online_rotate": online_rotate,
        "clip_search_y": clip_search_y
    }

    return {
        "fc_kwargs": setup_linear_args(**filter_kwargs(kwargs, ["preset", "preset_x", "preset_w", "preset_NL", "online_rotate", "clip_search_y"])),
        "embed_kwargs": setup_embed_args(**filter_kwargs(kwargs, ["preset", "preset_w"])),
        "attn_kwargs": setup_atten_args(**filter_kwargs(kwargs, ["preset", "preset_x", "preset_w", "preset_Kv", "preset_NL", "online_rotate"])),
        "mlp_kwargs": setup_mlp_args(**filter_kwargs(kwargs, ["preset", "preset_NL"])),
        "rms_kwargs": setup_norm_args(**filter_kwargs(kwargs, ["preset", "preset_NL"])),
    }
