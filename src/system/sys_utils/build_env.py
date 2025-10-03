from build_sys_tools import *
import logging
from cfl_cocotb import SRC_PATH
from cfl_tools.logger import get_logger
from memory_mapping.rand_gen import RandomTensorGenerator
from utils.load_config import load_svh_settings

logger = get_logger("testbench")
logger.setLevel(logging.DEBUG)

def build_fake_sim_env(data_size=1024):
    # TODO: Add an automatic to actually gen the sim env.
    parser = argparse.ArgumentParser(description="Build simulation environment")
    parser.add_argument('--asm', type=str, required=True, help='Path to assembly file')
    parser.add_argument('--data', type=str, default=None, help='Output directory for build files')
    args = parser.parse_args()
    args.path = Path(PROJECT_PATH / "test" / "Instr_Level_Benchmark" / f"{args.asm}.asm")
    init_mem(args)
    config_settings = load_svh_settings(str(SRC_PATH / "definitions" / "configuration.svh"))
    precision_settings = load_svh_settings(str(SRC_PATH / "definitions" / "precision.svh"))
    asm_file = Path(PROJECT_PATH / "test" / "Instr_Level_Benchmark" / f"{args.asm}.asm")

    data_config = {
        "tensor_size": [1, data_size],
        "block_size" : [1, precision_settings["BLOCK_DIM"]],
    }

    quant_config = {
            "exp_width": precision_settings["ACT_MXFP_EXP_WIDTH"],
            "man_width": precision_settings["ACT_MXFP_MANT_WIDTH"],
            "exp_bias_width": precision_settings["MX_SCALE_WIDTH"],
            "block_size": data_config["block_size"],
            "skip_first_dim": False,
        }
    if args.data is None:
        raw_data = RandomTensorGenerator(
            shape=tuple(data_config["tensor_size"]),
            directory=PROJECT_PATH / "test" / Path(asm_file).parent.stem / "build",
            filename="test_projection_data.pt",
            quant_config=quant_config
        )
    else:
        # TODO: Write Load Weight Function, loading the data from pretrained model.
        raw_data = None

    raw_data.tensor_gen()
    data = raw_data.tensor_load()

    blocks, bias = raw_data.quantize_tensor(data)
    generate_golden_result(data, logger, precision_settings, data_config)
    env_setup(blocks, bias, asm_file, data_config, quant_config, hbm_row_width=config_settings["HBM_WIDTH"])

if __name__ == "__main__":
    build_fake_sim_env()
    pass