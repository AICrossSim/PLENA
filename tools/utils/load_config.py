import re
import toml

def load_svh_settings(file_path):
    """
    Parse SystemVerilog `parameter` definitions in an .svh/.sv file
    """
    param_pattern = re.compile(r'\s*parameter\s+(\w+)\s*=\s*([^;]+);')
    hardware_settings = {}

    with open(file_path, "r") as f:
        for line in f:
            match = param_pattern.match(line)
            if match:
                name, value_str = match.groups()
                value_str = value_str.strip()
                # Try integer conversion first
                try:
                    value = int(value_str)
                except ValueError:
                    # Fallback to raw string (could be expression or real number)
                    continue
                hardware_settings[name] = value
    return hardware_settings


def load_json(file_path):
    """
    Load machine learning model configuration from a JSON file.
    """
    import json
    with open(file_path, "r") as f:
        ml_config = json.load(f)
    return ml_config


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


def patch_config_svh_from_toml(
    toml_path: str,
    section: str,
    svh_path: str
):
    """Configures the SystemVerilog header file based on the TOML [active] configuration."""
    pkg_name = {"CONFIG": "configuration_pkg", "PRECISION": "precision_pkg", "INSTR": "instruction_pkg"}.get(section, None)

    with open(toml_path, "r") as f:
        data = toml.load(f)
    toml_config = data.get(section, {})

    if not toml_config:
        raise ValueError(f"No {section} section found in TOML")
    mode = "active"
    hardware_settings = {
        param: values.get(mode)
        for param, values in toml_config.items()
        if mode in values
    } 

    with open(svh_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    in_configuration_pkg = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith(f"package {pkg_name}"):
            in_configuration_pkg = True
        elif stripped.startswith("endpackage") and in_configuration_pkg:
            in_configuration_pkg = False

        if in_configuration_pkg:
            match = re.match(r'\s*parameter\s+(\w+)\s*=.*;', line)
            if match:
                param_name = match.group(1)
                if param_name in hardware_settings:
                    new_value = hardware_settings[param_name]
                    indent = re.match(r'^(\s*)', line).group(1)
                    new_line = f"{indent}parameter   {param_name} = {new_value};\n"
                    new_lines.append(new_line)
                    continue

        new_lines.append(line)

    with open(svh_path, "w") as f:
        f.writelines(new_lines)