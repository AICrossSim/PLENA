import toml
import re
import os
import argparse
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
    config_params: dict = None
):
    with open(toml_path, "r") as f:
        data = toml.load(f)
        toml_config = data.get("CONFIG", {})

        if not toml_config:
            raise ValueError("No [CONFIG] section found in TOML")

        if mode is not None and mode != "active":
            found_any = False
            for param, values in toml_config.items():
                if mode in values:
                    found_any = True
                    # Copy mode value to active
                    toml_config[param]['active'] = values[mode]
            if not found_any:
                raise ValueError(f"Mode '{mode}' not found in any parameters.")
            
        if config_params is not None:
            for param, value in config_params.items():
                if param in toml_config:
                    toml_config[param]['active'] = value
                else:
                    raise ValueError(f"Parameter '{param}' not found in TOML.")
        
        # Write back the modified toml
        data["CONFIG"] = toml_config
        with open(toml_path, "w") as f:
            toml.dump(data, f)
        print(f"Updated 'active' values in {toml_path} with mode '{mode}'.")


def main():
    parser = argparse.ArgumentParser(description="Update TOML active values.")
    parser.add_argument("--toml_file",  default=None, help="Path to TOML file")
    parser.add_argument("--param",      default=None, help="Parameter to update or '*' for all")
    parser.add_argument("--value",      default=None, help="New value to set as active")
    parser.add_argument("--mode",       default=None, help="Mode to use for copying (e.g. ASIC, SIMULATION, etc.)")

    args = parser.parse_args()

    print("TOML FILE:", args.toml_file)
    print("PARAM:", args.param)
    print("VALUE:", args.value)
    print("MODE:", args.mode)
    pass
        


if __name__ == "__main__":
    main()