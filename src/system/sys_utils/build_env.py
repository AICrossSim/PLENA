from build_sys_tools import *
import logging
from cfl_cocotb import SRC_PATH
from cfl_tools.logger import get_logger
from memory_mapping.rand_gen import Random_MXFP_Tensor_Generator
from utils.load_config import load_svh_settings
from pathlib import Path

logger = get_logger("testbench")
logger.setLevel(logging.DEBUG)

def build_fake_sim_env(data_size=256):
    parser = argparse.ArgumentParser(description="Build simulation environment")
    parser.add_argument('--mode', type=str, default=None, help='Mode for Simulation')
    parser.add_argument('--asm', type=str, required=True, help='Path to assembly file')
    parser.add_argument('--data', type=str, default=None, help='Output directory for build files')
    args = parser.parse_args()
    
    config_settings = load_svh_settings(str(SRC_PATH / "definitions" / "configuration.svh"))
    precision_settings = load_svh_settings(str(SRC_PATH / "definitions" / "precision.svh"))
    if args.mode == "behave_sim":
        asm_file = Path(PROJECT_PATH / "behavioral_simulator" / "testbench" / "build" / "generated_asm_code.asm")
    else:
        asm_file = Path(PROJECT_PATH / "test" / "Instr_Level_Benchmark" / f"{args.asm}.asm")
    
    init_mem(Path(asm_file.parent) / "build")

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

    if args.mode != "behave_sim":
        grp_blocks = []
        grp_bias = []
        raw_data = Random_MXFP_Tensor_Generator(
            shape=tuple(data_config["tensor_size"]),
            quant_config=quant_config,
            config_settings=config_settings,
            directory=PROJECT_PATH / "test" / Path(asm_file).parent.stem / "build",
            filename= Path(f"{args.asm}/fake_test_raw_data.pt")
        )
        raw_data.tensor_gen()
        data = raw_data.tensor_load()
        blocks, bias = raw_data.quantize_tensor(data)
        grp_blocks.append(blocks)
        grp_bias.append(bias)
    else:
        # The provided path (args.data) is a directory. Enumerate all .pt and .pth files within,
        # then load and quantize all of them. Collect the results in dictionaries keyed by filename.
        target_dir = PROJECT_PATH / "behavioral_simulator" / "testbench" / "build"
        pt_files = list(target_dir.glob("*.pt")) + list(target_dir.glob("*.pth"))
        grp_blocks = []
        grp_bias = []
        for pt_file in pt_files:
            print("loading file", pt_file)
            file_raw_data = Random_MXFP_Tensor_Generator(
                shape=tuple(data_config["tensor_size"]),
                quant_config=quant_config,
                config_settings=config_settings,
                directory=target_dir,
                filename=pt_file
            )
            file_tensor = file_raw_data.tensor_load()
            blocks, bias = file_raw_data.quantize_tensor(file_tensor)
            for block, b in zip(blocks, bias):
                grp_blocks.append(block)
                grp_bias.append(b)
    # generate_golden_result(data, logger, precision_settings, data_config)
    env_setup(grp_blocks, grp_bias, asm_file, data_config, quant_config, hbm_row_width=config_settings["HBM_WIDTH"])

if __name__ == "__main__":
    build_fake_sim_env()
    pass