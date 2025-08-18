from ...tools.cost_model.latency import instr_latency_model
from ...tools.cost_model.utilisation import utilisation_model
from ...acc_simulator.cli.acc_sim import llama_eval
from .utils import parse_precision_config, build_llama_eval_kwargs, load_toml_config

CONFIG_PATH     = "src/definitions/configuration.svh"
PRECISION_PATH  = "src/definitions/precision.svh"
TOML_PATH       = "src/definitions/config.toml"
UNIT_INFO_PATH  = "tools/cost_model/utilisation/individual_units_lib.json"
CUSTOM_ISA_PATH = "tools/cost_model/latency/customISA_lib.json"

MODEL_CONFIG_LIB = {"meta-llama/Llama-3.2-1B": "doc/Model_Lib/llama-3.1-8b.json",
         "meta-llama/Meta-Llama-3-8B": "doc/Model_Lib/llama-3-8b.json"}

GPTQ_MODEL_CKPT_PATH = "ckpts"


def get_area(config_dict: dict) -> float:
    utilisation = utilisation_model(CONFIG_PATH, PRECISION_PATH, UNIT_INFO_PATH)
    # test_from_toml = load_toml_config(TOML_PATH, "active")
    area = utilisation.obtain_resource_utilisation(config_dict)
    print(f"Resource Utilisation: {area}")
    return area


def get_latency(config_dict: dict, 
                model_name: str = "meta-llama/Llama-3.2-1B") -> float:
    model = instr_latency_model(CONFIG_PATH, CUSTOM_ISA_PATH, MODEL_CONFIG_LIB[model_name])
    # test_from_toml = load_toml_config(toml_path, "active")
    overall_latency = model.obtain_overall_latency(config_dict)
    print(f"Overall latency: {overall_latency} seconds")
    return overall_latency
    

def get_accuracy(config_dict: dict,
                 model_name: str = "meta-llama/Llama-3.2-1B",
                 model_flag: int = None) -> float:
    
    kwargs = build_llama_eval_kwargs(precision=config_dict, 
                                     preset="XqWqBqKVqNL", 
                                     model_name=model_name,
                                     full_system_sim=False,
                                     gptq_ckpt_dir=GPTQ_MODEL_CKPT_PATH,
                                     model_flag=model_flag)

    accuracy = llama_eval(**kwargs)
    # Assume eval_harness is not enabled for now, only searching over ppl for prefilling 
    return accuracy["ppl"]

