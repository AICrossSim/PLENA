import toml
import json

def load_hardware_settings(
        toml_path: str = "config.toml",
        section: str = "CONFIG"
):
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