
import toml
import os
import json
from pathlib import Path
from utils import load_toml_config, load_json, load_svh_settings



class utilisation_model:
    def __init__(self, hardware_settings_file: str = "config.toml", precision_settings_file: str = "precision.toml", unit_info_file: str = "unit_info.json"):
        self.hardware_settings_file = hardware_settings_file
        self.precision_settings_file = precision_settings_file
        self.unit_info = load_json(unit_info_file)
    
    def obtain_resource_utilisation(self):
        resource_utilisation = 0
        config_settings = load_svh_settings(self.hardware_settings_file)
        precision_settings = load_svh_settings(self.precision_settings_file)
        for unit, info in self.unit_info.items():
            unit_config = {**config_settings, **precision_settings}
            if "Coefficients" in info and "Relationship" in info:
                unit_config.update(info["Coefficients"])
                relationship = info["Relationship"]
                resource_utilisation += eval(relationship, {}, unit_config)
        return resource_utilisation



if __name__ == "__main__":
    config_parent_path = Path(__file__).resolve().parents[3]
    config_path = os.path.join(config_parent_path, "src/definitions/configuration.svh")
    precision_path = os.path.join(config_parent_path, "src/definitions/precision.svh")
    unit_info_file = os.path.join(config_parent_path, "tools/cost_model/utilisation/individual_units_lib.json")
    utilisation = utilisation_model(config_path, precision_path, unit_info_file)
    print(f"Resource Utilisation: {utilisation.obtain_resource_utilisation()}")