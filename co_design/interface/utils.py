import toml

def parse_precision_config(config_path: str) -> dict:
    """Parse TOML and extract relevant 'active' values from PRECISION section."""
    toml_data = toml.load(config_path)
    precision_cfg = toml_data.get("PRECISION", {})

    extracted = {}
    for key, subdict in precision_cfg.items():
        if isinstance(subdict, dict) and "active" in subdict:
            extracted[key] = subdict["active"]
    # print(extracted)
    return extracted

def build_llama_eval_kwargs(precision: dict, preset: str = "XqWqBqKVqNLq", minifloat: str = None) -> dict:
    # Build MXFP suffix from scale and block
    scale = precision["MXFP_SCALE_WIDTH"]
    block = precision["BLOCK_DIM"]
    suffix = f"B{block}_S{scale}"

    # Prepare the kwargs
    return {
        "model_name": "meta-llama/Llama-3.2-1B",
        "preset": preset,
        "preset_mxfp_X": f"MXFP_E{precision['ACT_MXFP_EXP_WIDTH']}M{precision['ACT_MXFP_MANT_WIDTH']}_{suffix}",
        "preset_mxfp_W": f"MXFP_E{precision['WT_MXFP_EXP_WIDTH']}M{precision['WT_MXFP_MANT_WIDTH']}_{suffix}",
        "preset_mxfp_Kv": f"MXFP_E{precision['KV_MXFP_EXP_WIDTH']}M{precision['KV_MXFP_MANT_WIDTH']}_{suffix}",
        "preset_minifloat_NL": minifloat or f"FP_E{precision['V_FP_EXP_WIDTH']}M{precision['V_FP_MANT_WIDTH']}",
        "model_parallel": False,
        "enable_eval_harness": False,
    }

def write_active_config_to_toml(config_path: str, updated_values: dict, output_path: str = None):
    """
    Updates the 'active' fields in CONFIG / PRECISION / INSTR sections
    based on sampled 'updated_values', and writes back to TOML.
    """
    section_names = ["CONFIG", "PRECISION", "INSTR"]
    toml_data = toml.load(config_path)

    for section in section_names:
        if section in toml_data:
            for param, value in updated_values.items():
                if param in toml_data[section]:
                    toml_data[section][param]["active"] = value

    if output_path is None:
        output_path = config_path  # Overwrite in-place

    with open(output_path, "w") as f:
        toml.dump(toml_data, f)

    print(f"[INFO] Updated active values written to {output_path}")

def load_toml_config(file_path, mode=None):
    section_to_load = ["CONFIG", "PRECISION", "INSTR"]
    config = {}

    with open(file_path, "r") as f:
        full_toml = toml.load(f)
    for section in section_to_load:
        toml_config = full_toml.get(section, {})
        if toml_config:
            hardware_settings = {
                param: values.get(mode)
                for param, values in toml_config.items()
                if mode in values
            }
            config.update(hardware_settings)
    return config
