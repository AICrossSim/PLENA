
import torch
import argparse
from cfl_tools import PROJECT_PATH
from pathlib import Path
from assembler.assembly_to_binary import AssemblyToBinary
from assembler.memory_mapping.memory_map import map_fp_data_to_fake_hbm, map_data_to_fake_hbm
from assembler.memory_mapping.rand_gen import RandomTensorGenerator

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True, help='Path to the test assembly file')
    args = parser.parse_args()
    return args

def instruction_mapping_pipeline(blocks, bias, test_path: str, quant_config):

    torch.manual_seed(52)
    isa_file_path = PROJECT_PATH / 'src' / 'definitions' / 'operation.svh'
    asm_file_path = test_path

    build_folder = PROJECT_PATH/ 'test' /Path(asm_file_path).parent.stem / 'build'
    test_file_name = Path(asm_file_path).stem
    build_folder = build_folder / f'{test_file_name}'
    build_folder.mkdir(parents=True, exist_ok=True)

    assembler = AssemblyToBinary(str(isa_file_path))
    assembler.generate_binary(asm_file_path, build_folder / f'{test_file_name}.mem')

    filename = "test_projection_data.pt"
    torch.manual_seed(52)
    
    map_data_to_fake_hbm(   blocks=blocks,
                            element_width=quant_config["exp_width"] + quant_config["man_width"] + 1,
                            block_width=(quant_config["exp_width"] + quant_config["man_width"] + 1) * 4,
                            bias=bias,
                            bias_width=quant_config["exp_bias_width"],
                            combined_blk_dim = 2,
                            directory=build_folder,
                            append=False,
                            hbm_row_width=256)


if __name__ == "__main__":
    args = parse_args()
    quant_config_high = {
            "exp_width": 4,
            "man_width": 3,
            "exp_bias_width": 8,
            "block_size": [1, 4],
            "skip_first_dim": False,
        }
    rand_gen_high = RandomTensorGenerator(
        shape=(1, 8),
        directory=PROJECT_PATH / "test" / Path(args.path).parent.stem / "build",
        filename="test_projection_data.pt",
        quant_config=quant_config_high
    )
    
    # Expect shape, blocks.shape = (32, 4), bias.shape = (32, 1)
    rand_gen_high.tensor_gen()
    data = rand_gen_high.tensor_load()
    blocks, bias = rand_gen_high.quantize_tensor(data)
    instruction_mapping_pipeline(blocks, bias, args.path, quant_config_high)