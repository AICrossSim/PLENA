
import torch
import argparse
from cfl_tools import PROJECT_PATH
from pathlib import Path
from assembler.assembly_to_binary import AssemblyToBinary
from assembler.memory_mapping.memory_map import map_fp_data_to_fake_hbm, map_data_to_fake_hbm

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True, help='Path to the test assembly file')
    args = parser.parse_args()
    return args

def instruction_mapping_pipeline(packed_hbm_tensor: torch.Tensor, test_path: str):

    torch.manual_seed(52)
    isa_file_path = PROJECT_PATH / 'src' / 'definitions' / 'operation.svh'
    asm_file_path = test_path

    build_folder = PROJECT_PATH/ 'test' /Path(asm_file_path).parent.stem / 'build'
    test_file_name = Path(asm_file_path).stem
    build_folder = build_folder / f'{test_file_name}'
    build_folder.mkdir(parents=True, exist_ok=True)

    assembler = AssemblyToBinary(str(isa_file_path))
    assembler.generate_binary(asm_file_path, build_folder / f'{test_file_name}.mem')

    quant_config_high = {
        "exp_width": 4,
        "man_width": 3,
        "exp_bias_width": 7,
        "block_size": [1, 4],
        "skip_first_dim": False,
    }
    rand_gen_high = RandomTensorGenerator(
        shape=(8, 8),
        directory=directory,
        filename=filename,
        quant_config=quant_config_low
    )
    
    # Expect shape, blocks.shape = (32, 4), bias.shape = (32, 1)
    rand_gen_high.tensor_gen()
    weight = rand_gen_high.tensor_load()
    blocks, bias = rand_gen_high.quantize_tensor(weight[:8, :])
    map_data_to_fake_hbm(   blocks=blocks,
                            element_width=quant_config_high["exp_width"] + quant_config_high["man_width"] + 1,
                            block_width=(quant_config_high["exp_width"] + quant_config_high["man_width"] + 1) * 4,
                            bias=bias,
                            bias_width=quant_config_high["exp_bias_width"],
                            combined_blk_dim = 2,
                            directory=fake_hbm_dir,
                            append=False,
                            hbm_row_width=256)


if __name__ == "__main__":
    args = parse_args()
    tensor = torch.randn(1, 8)
    from cfl_cocotb.torch_fp_conversion import fp_2_bin
    _, packed_hbm_tensor = fp_2_bin(tensor, 5, 10)
    instruction_mapping_pipeline(packed_hbm_tensor, args.path)
