import toml

def get_bit_width(fmt: str) -> int:
    fmt = fmt.upper()

    if fmt.startswith("MXFP"):
        # Example: MXFP_E5M2 → exponent=5, mantissa=2
        # Remove the "MXFP_" prefix
        fmt_body = fmt.split("_")[1]  # "E5M2"
        # Remove leading 'E', then split by 'M'
        exp_str, mant_str = fmt_body[1:].split("M")  # "5", "2"
        exp = int(exp_str)
        mant = int(mant_str)
        return exp + mant + 1 

    elif fmt.startswith("MXINT"):
        # Example: MXINT8 → 8 bits total
        bits = int(fmt.replace("MXINT_", ""))
        return bits
    else:
        raise ValueError(f"Unknown format: {fmt}")


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

def build_llama_eval_kwargs(precision: dict, 
                            model_name,
                            gptq_ckpt_dir,
                            preset: str = "XqWqBqKVqNLq", 
                            full_system_sim: bool = True) -> dict:
    # Build MX suffix from scale and block
    scale = 8
    block = 16
    suffix = f"B{block}_S{scale}"
    
    if full_system_sim:
        minifloat = f"FP_E{precision['FP_EXP_WIDTH']}M{precision['FP_MANT_WIDTH']}"
    else:
        minifloat = None

    # Prepare the kwargs
    return {
        "model_name": model_name,
        "preset": preset,
        "preset_X": f"{precision['ACT_ELEMENT_WIDTH']}_{suffix}",
        "preset_W": f"MXINT_4_{suffix}",
        "preset_Kv": f"{precision['KV_ELEMENT_WIDTH']}_{suffix}",
        "preset_NL": minifloat,
        "model_parallel": False,
        "enable_eval_harness": False,
        "use_gptq": True,
        "online_rotate": True,
        "full_system_sim": full_system_sim,
        "gptq_ckpt_dir": gptq_ckpt_dir,
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
