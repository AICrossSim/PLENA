import toml
import re
import os
import sys

def patch_config_svh_from_toml(
    mode : str,
    toml_path: str,
    svh_path: str
):
    """Configures the SystemVerilog header file based on the TOML [active] configuration."""

    with open(toml_path, "r") as f:
        data = toml.load(f)
    toml_config = data.get("CONFIG", {})

    if not toml_config:
        raise ValueError("No [CONFIG] section found in TOML")

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

        if stripped.startswith("package configuration_pkg"):
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

def configure_toml_file(
    mode: str,
    toml_path: str = "config.toml",
    svh_path: str = "configuration.svh"
):
    with open(toml_path, "r") as f:
        data = toml.load(f)
        toml_config = data.get("CONFIG", {})

        if not toml_config:
            raise ValueError("No [CONFIG] section found in TOML")

        if mode is not None and not mode == "active":
            hardware_settings = {
                param: values.get(mode)
                for param, values in toml_config.items()
                if mode in values
            } 


        




if __name__ == "__main__":
    parent_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(parent_path, "config.toml")
    svh_path    = os.path.join(parent_path, "configuration.svh")
    patch_config_svh_from_toml(config_path, svh_path)