from ...tools.utils.config import patch_config_svh_from_toml
from ...tools.cost_model.latency import instr_latency_model
from ...tools.cost_model.utilisation import utilisation_model
from ...acc_simulator.cli.acc_sim import llama_eval
from .utils import parse_precision_config, build_llama_eval_kwargs

SAMPELED_CONFIG_TOML = "config/config_sampled.toml"
UNIT_INFO_FILE = "tools/cost_model/utilisation/individual_units_lib.json"
CONFIG_PATH_SVH = "config/configuration.svh"
CUSTOM_ISA_PATH = "tools/cost_model/latency/customISA_lib.json"
MODEL_CONFIG_PATH = "doc/Model_Lib/llama-3.1-8b.json"

def get_area():
    config_path = SAMPELED_CONFIG_TOML
    unit_info_file = UNIT_INFO_FILE
    utilisation = utilisation_model(config_path, unit_info_file)
    print(f"Resource Utilisation: {utilisation.obtain_resource_utilisation()}")
    return utilisation.obtain_resource_utilisation()


def get_latency():
    toml_path = SAMPELED_CONFIG_TOML
    config_path = CONFIG_PATH_SVH
    patch_config_svh_from_toml(
        toml_path=toml_path,
        section="CONFIG",
        svh_path=config_path)
    patch_config_svh_from_toml(
        toml_path=toml_path,
        section="INSTR",
        svh_path=config_path)
    
    custom_isa_path  = CUSTOM_ISA_PATH
    model_config_path = MODEL_CONFIG_PATH
    model = instr_latency_model(config_path, custom_isa_path, model_config_path)
    overall_latency = model.obtain_overall_latency()
    print(f"Overall latency: {overall_latency} seconds")
    return overall_latency
    

def get_accuracy():
    # TODO: set up gptq checkpoints
    model_path = ""
    precision = parse_precision_config(SAMPELED_CONFIG_TOML)
    kwargs = build_llama_eval_kwargs(precision)

    # print("Calling llama_eval with arguments:")
    # for k, v in kwargs.items():
    #     print(f"  {k} = {v}")

    accuracy = llama_eval(**kwargs)
    # Assume eval_harness is not enabled for now
    return accuracy["ppl"]

