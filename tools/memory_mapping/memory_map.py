from memory_mapping.rand_gen import RandomTensorGenerator
import torch
import os

def map_block_to_value(block, data_width):
    if data_width % 4 != 0:
        raise ValueError("data_width must be a multiple of 4 for hex representation.")

    hex_digits = data_width // 4  # e.g., 32 bits = 8 hex digits
    return ''.join(f"{element:0{hex_digits}X}" for element in block)

def map_scale_to_value(scale, data_width):
    if data_width % 4 != 0:
        raise ValueError("data_width must be a multiple of 4 for hex representation.")

    hex_digits = data_width // 4  # e.g., 32 bits = 8 hex digits
    return f"{scale:0{hex_digits}X}"

def map_data_to_fake_hbm(blocks, element_width, block_width, bias, bias_width, directory, hbm_row_width=64):

    """
    Maps the quantized blocks and bias to a fake HBM memory structure.
    """
    num_blocks_per_row = hbm_row_width // block_width
    num_bias_per_row = hbm_row_width // bias_width

    if not os.path.exists(directory):
        os.makedirs(directory)
    
    with open(os.path.join(directory, "hbm_ele.mem"), "w") as f:
        insert_block_row = ""
        index_in_row = 0
        for i, block in enumerate(blocks):
            insert_block_row += map_block_to_value(block, element_width)
            index_in_row += 1
            if index_in_row == num_blocks_per_row:
                f.write("0x" + insert_block_row + "\n")
                insert_block_row = ""
                index_in_row = 0
    # Save Bias to HBM file            
    with open(os.path.join(directory, "hbm_scale.mem"), "w") as f:
        insert_bias_row = ""
        index_in_row = 0
        for i, b in enumerate(bias):
            insert_bias_row += map_scale_to_value(b, bias_width)
            index_in_row += 1
            if index_in_row == num_bias_per_row:
                f.write("0x" + insert_bias_row + "\n")
                insert_bias_row = ""
                index_in_row = 0


if __name__ == "__main__":
    directory = "../../test/weight"
    fake_hbm_dir = "../../test/load_mem"
    filename = "test_projection_data.pt"
    torch.manual_seed(52)
    quant_config = {
        "exp_width": 4,
        "man_width": 3,
        "exp_bias_width": 16,
        "block_size": [1, 4],
        "skip_first_dim": False,
    }
    rand_gen = RandomTensorGenerator(
        shape=(16, 8),
        directory=directory,
        filename=filename,
        quant_config=quant_config
    )
    
    # Expect shape, blocks.shape = (16, 2, 4), bias.shape = (16, 2)
    rand_gen.tensor_gen()
    weight = rand_gen.tensor_load()
    blocks, bias = rand_gen.quantize_tensor(weight)
    map_data_to_fake_hbm(   blocks=blocks,
                            element_width=quant_config["exp_width"] + quant_config["man_width"] + 1,
                            block_width=(quant_config["exp_width"] + quant_config["man_width"] + 1) * 4,
                            bias=bias,
                            bias_width=quant_config["exp_bias_width"],
                            directory=fake_hbm_dir,
                            hbm_row_width=256)

