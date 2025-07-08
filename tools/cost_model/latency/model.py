import toml
import json
import os
from pathlib import Path
from math import log2
import re

# def load_hardware_settings(
#         toml_path: str = "config.toml",
#         section: str = "CONFIG"
# ):
#     with open(toml_path, "r") as f:
#         data = toml.load(f)
#         toml_config = data.get(section, {})
    
#     if not toml_config:
#         raise ValueError(f"No {section} section found in TOML")
#     mode = "active"
#     hardware_settings = {
#         param: values.get(mode)
#         for param, values in toml_config.items()
#         if mode in values
#     } 
#     hardware_settings["SA_ACC_CYCLES"] = int(log2(hardware_settings["MLEN"] / hardware_settings["BLEN"]) + 1)
#     return hardware_settings

def load_hardware_settings(file_path):
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
    hardware_settings["SA_ACC_CYCLES"] = int(log2(hardware_settings["MLEN"] / hardware_settings["BLEN"]) + 1)
    return hardware_settings

def load_custom_isa_lib(
        json_path: str
):
    with open(json_path, "r") as f:
        custom_isa_lib = json.load(f)
    return custom_isa_lib


class instr_info:
    def __init__(self, name, alone, pipelined, configs):
        self.name       = name
        self.alone      = eval(alone, {}, configs)
        self.pipelined  = eval(pipelined, {}, configs)

def build_instr_model(
    hardware_settings_file: str = "configuration.svh",
    custom_isa_lib_file:    str = "customISA_lib.json"
):
    hardware_settings = load_hardware_settings(hardware_settings_file)
    custom_isa_lib = load_custom_isa_lib(custom_isa_lib_file)

    instr_latency_model = {}
    for instr_name, instr_data in custom_isa_lib.items():
        if "alone" in instr_data and "pipelined" in instr_data:
            alone = instr_data["alone"]
            pipelined = instr_data["pipelined"]
            instr_latency_model[instr_name] = instr_info(instr_name, alone, pipelined, hardware_settings)
        else:
            raise ValueError(f"Instruction '{instr_name}' does not have 'alone' or 'pipelined' fields.")
    
    return instr_latency_model


class instr_latency_model:
    def __init__(self, hardware_settings_file: str = "config.toml", custom_isa_lib_file: str = "customISA_lib.json"):
        self.instr_model = build_instr_model(hardware_settings_file, custom_isa_lib_file)

    def get_instr_info(self, instr_name):
        return self.model.get(instr_name, None)
    
    def obtain_pipelined_latency(self, output_file: str = "instr_latency_model.json"):
        pipelined_latency = {
            instr_name: {
                "pipelined": instr_info.pipelined
            }
            for instr_name, instr_info in self.instr_model.items()
        }
        
        with open(output_file, "w") as f:
            json.dump(pipelined_latency, f, indent=4)
        
        print(f"Average latency model saved to {output_file}")
    
    def obtain_alone_latency(self, output_file: str = "instr_alone_latency_model.json"):
        alone_latency = {
            instr_name: {
                "alone": instr_info.alone
            }
            for instr_name, instr_info in self.instr_model.items()
        }
        
        with open(output_file, "w") as f:
            json.dump(alone_latency, f, indent=4)
        
        print(f"Alone latency model saved to {output_file}")



if __name__ == "__main__":
    config_parent_path = Path(__file__).resolve().parents[3]
    config_path = os.path.join(config_parent_path, "src/definitions/configuration.svh")
    custom_isa_parent_path  = os.path.dirname(os.path.abspath(__file__))
    custom_isa_path         = os.path.join(custom_isa_parent_path, "customISA_lib.json")

    model = instr_latency_model(config_path, custom_isa_path)
    model.obtain_pipelined_latency  ("instr_pipelined_ver_latency_model.json")
    model.obtain_alone_latency      ("instr_alone_ver_latency_model.json")