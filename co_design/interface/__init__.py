from . import interface

CONFIG_PATH     = "src/definitions/configuration.svh"
PRECISION_PATH  = "src/definitions/precision.svh"
TOML_PATH       = "src/definitions/config.toml"
UNIT_INFO_PATH  = "tools/cost_model/utilisation/individual_units_lib.json"
CUSTOM_ISA_PATH = "tools/cost_model/latency/customISA_lib.json"

MODEL_CONFIG_LIB = {"meta-llama/Llama-3.2-1B": "doc/Model_Lib/llama-3.1-8b.json",
         "meta-llama/Meta-Llama-3-8B": "doc/Model_Lib/llama-3-8b.json"}


__all__ = ["interface"]