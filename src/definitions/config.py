import toml
import re
import os
import argparse
import sys

def update_global_define(file_path, selected_mode):
    modes = ["SIMULATION", "ASIC", "FPGA"]
    if selected_mode not in modes:
        print(f"Error: Unsupported mode '{selected_mode}'. Must be one of {modes}.")
        return

    with open(file_path, 'w') as f:
        f.write("`ifndef GLOBAL_DEFINE_VH\n")
        f.write(f"`define {selected_mode}\n")
        f.write("`endif\n")

    print(f"Updated {file_path} with mode {selected_mode}.")



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

def parse_config_string(config_str):
    param_dict = {}
    if config_str:
        pairs = config_str.strip().split()
        for pair in pairs:
            key, val = pair.split('=')
            param_dict[key.strip()] = int(val.strip())
    return param_dict


def modify_toml_file(
    mode: str,
    toml_path: str = "plena_settings.toml",
    section: str = "CONFIG",
    config_params: dict = None
):
    with open(toml_path, "r") as f:
        data = toml.load(f)
        toml_config = data.get(section, {})

        if not toml_config:
            raise ValueError(f"No {section} section found in TOML")

        if mode is not None:
            found_any = False
            for param, values in toml_config.items():
                if mode in values:
                    found_any = True
                    # Copy mode value to active
                    toml_config[param]['active'] = values[mode]
            if not found_any:
                raise ValueError(f"Mode '{mode}' not found in any parameters.")
        else:
            for param, values in toml_config.items():
                if mode in values:
                    found_any = True
                    # Copy mode default to active first
                    toml_config[param]['active'] = values["default"]
            
        if config_params is not None:
            for param, value in config_params.items():
                if param in toml_config:
                    toml_config[param]['active'] = value
                else:
                    raise ValueError(f"Parameter '{param}' not found in TOML.")
        
        # Write back the modified toml
        data[section] = toml_config
        with open(toml_path, "w") as f:
            toml.dump(data, f)
        print(f"Updated 'active' values in {toml_path} with mode '{mode}'.")

def generate_plena_sys_config_from_toml(toml_path: str, output_json_path: str = None):
    """
    Generates a JSON config file (plena_sys_config.json) based on the current values in the given TOML config file.
    """
    import json
    import os

    # Try to load TOML config (expecting 'CONFIG' as a main section)
    with open(toml_path, "r") as f:
        data = toml.load(f)
    config = data.get("CONFIG", {})
    precision = data.get("PRECISION", {})

    # Helper to get the "active" value or fallback to default or cast to int if string
    def get(param, default=None):
        val = config.get(param, {})
        if isinstance(val, dict):
            result = val.get("active", val.get("default", default))
        else:
            result = val if val is not None else default
        try:
            return int(result)
        except Exception:
            return result

    # Handle possible var names, fallback if not found (for demo)
    mlen = get("MLEN", 512)
    hlen = get("HLEN", 32)
    blen = get("BLEN", 32)
    vlen = get("VLEN", 4096)

    # Example of using precision config param (pick fp_type if present)
    fp_data_type = precision.get("FP_UNIT_TYPE", {}).get("active", "fp8") if precision else "fp8"
    mxfp_data_type = precision.get("MX_UNIT_TYPE", {}).get("active", "mxfp") if precision else "mxfp"

    # Prepare the JSON structure as in the reference
    json_conf = {
        "name": "PLENA",
        "device_count": 1,
        "interconnect": {},
        "device": {
            "frequency_Hz": 1e9,
            "compute_chiplet_count": 1,
            "compute_chiplet": {
                "physical_core_count": 128,
                "core_count": mlen // hlen if hlen else 1,
                "process_node": "7nm",
                "core": {
                    "sublane_count": 1,
                    "systolic_array": {
                        "array_width": hlen,
                        "array_height": blen,
                        "data_type": mxfp_data_type,
                        "mac_per_cycle": 1,
                    },
                    "vector_unit": {
                        "vector_width": vlen // (mlen // hlen) if mlen and hlen else vlen,
                        "flop_per_cycle": 4,
                        "data_type": fp_data_type,
                        "int32_count": 0,
                        "fp16_count": 0,
                        "fp32_count": 0,
                        "fp64_count": 0
                    },
                    "register_file": {
                        "num_reg_files": 1,
                        "num_registers": 32,
                        "register_bitwidth": 32,
                        "num_rdwr_ports": 2
                    },
                    "SRAM_KB": vlen
                }
            },
            "memory_protocol": "HBM2e",
            "_memory_protocol_list": [
                "HBM2e",
                "DDR4",
                "DDR5",
                "PCIe4",
                "PCIe5"
            ],
            "io": {
                "process_node": "7nm",
                "global_buffer_MB": 48,
                "physical_global_buffer_MB": 48,
                "global_buffer_bandwidth_per_cycle_byte": 5120,
                "memory_channel_physical_count": 6,
                "memory_channel_active_count": 5,
                "pin_count_per_channel": 1024,
                "bandwidth_per_pin_bit": 3.2e9
            },
            "memory": {
                "total_capacity_GB": 80
            }
        }
    }

    if output_json_path is None:
        parent_path = os.path.dirname(os.path.abspath(__file__))
        output_json_path = os.path.join(parent_path, "plena_sys_config.json")

    with open(output_json_path, "w") as fout:
        json.dump(json_conf, fout, indent=4)
    print(f"Generated system config to {output_json_path}")




def main():
    parser = argparse.ArgumentParser(description="Update TOML active values.")
    parser.add_argument("--config", default=None, help="Parameter to update or '*' for all")
    parser.add_argument("--precision", default=None, help="Parameter to update or '*' for all")
    parser.add_argument("--mode",   default=None, help="Mode to use for copying (e.g. ASIC, SIMULATION, etc.)")
    args = parser.parse_args()
    config_settings = parse_config_string(args.config) if args.config else None
    precision_settings = parse_config_string(args.precision) if args.precision else None
    parent_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(parent_path, "plena_settings.toml")
    config_svh_path    = os.path.join(parent_path, "configuration.svh")
    precision_svh_path = os.path.join(parent_path, "precision.svh")

    if args.mode is not None:
        update_global_define(
            file_path=os.path.join(parent_path, "global_define.vh"),
            selected_mode=args.mode
        )

    if config_settings is not None:
        modify_toml_file(
            mode=args.mode,
            toml_path=config_path,
            section="CONFIG",
            config_params=config_settings
        )
        patch_config_svh_from_toml(
            toml_path=config_path,
            section="CONFIG",
            svh_path=config_svh_path
        )
    
    if precision_settings is not None:
        modify_toml_file(
            mode=args.mode,
            toml_path=config_path,
            section="PRECISION",
            config_params=precision_settings
        )
        patch_config_svh_from_toml(
            toml_path=config_path,
            section="PRECISION",
            svh_path=precision_svh_path
        )

if __name__ == "__main__":
    generate_plena_sys_config_from_toml("plena_settings.toml", "plena_sys_config.json")