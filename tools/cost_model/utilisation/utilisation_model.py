
import toml
import os
import json
from pathlib import Path
from utils import load_toml_config, load_json, load_svh_settings



class utilisation_model:
    def __init__(self, hardware_settings_file: str = "config.toml", precision_settings_file: str = "precision.toml", unit_info_file: str = "unit_info.json"):
        self.unit_info = load_json(unit_info_file)
        config_settings = load_svh_settings(hardware_settings_file)
        precision_settings = load_svh_settings(precision_settings_file)
        self.hardware_settings = {**config_settings, **precision_settings}
    def obtain_resource_utilisation(self, updated_config):
        resource_utilisation = 0
        hardware_settings = self.hardware_settings
        for key, value in updated_config.items():
            hardware_settings[key] = value

        for unit, info in self.unit_info.items():
            if "Coefficients" in info and "Relationship" in info:
                hardware_settings.update(info["Coefficients"])
                relationship = info["Relationship"]
                resource_utilisation += eval(relationship, {}, hardware_settings)
        return resource_utilisation



if __name__ == "__main__":
    import toml
    config_parent_path = Path(__file__).resolve().parents[3]
    config_path     = os.path.join(config_parent_path, "src/definitions/configuration.svh")
    precision_path  = os.path.join(config_parent_path, "src/definitions/precision.svh")
    toml_path       = os.path.join(config_parent_path, "src/definitions/config.toml")
    unit_info_file  = os.path.join(config_parent_path, "tools/cost_model/utilisation/individual_units_lib.json")
    
    utilisation = utilisation_model(config_path, precision_path, unit_info_file)
    test_from_toml = load_toml_config(toml_path, "active")
    print(f"Resource Utilisation: {utilisation.obtain_resource_utilisation(test_from_toml)}")