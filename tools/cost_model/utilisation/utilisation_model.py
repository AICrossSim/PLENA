
import toml
import os
import json
from pathlib import Path
from utils import load_toml_config, load_json


class individual_units:
    def __init__(self, relevant_parameters: dict):
        self.relevant_parameters = relevant_parameters


class utilisation_model:
    def __init__(self, hardware_settings_file: str = "config.toml", unit_info_file: str = "unit_info.json"):
        self.config_settings = load_toml_config(hardware_settings_file, mode="tunable_range")
        print(f"Loaded hardware settings: {self.config_settings}")
        unit_info = load_json(unit_info_file)
        for name, params in unit_info.items():
            setattr(self, name, individual_units(params))






if __name__ == "__main__":
    config_parent_path = Path(__file__).resolve().parents[3]
    config_path = os.path.join(config_parent_path, "src/definitions/config.toml")
    utilisation = utilisation_model(config_path)
    print(f"Utilisation model initialized with settings: {utilisation.config_settings}")