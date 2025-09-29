from memory_mapping.rand_gen import RandomTensorGenerator
from bitstring import BitArray
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


def map_fp_data_to_fake_hbm(packed_input, element_width, path):
    assert len(packed_input.shape) == 2, "packed_input must be a 2D tensor"
    with open(os.path.join(path, "hbm.mem"), "a") as f:
        row = ""
        index_in_row = 0
        for i, vector in enumerate(packed_input):
            for j, element in enumerate(vector):
                row = row + BitArray(uint=int(element), length=element_width).hex
            f.write("0x" + row + "\n")
            row = ""
            index_in_row += 1

def map_data_to_fake_hbm_for_rtl_sim(blocks, element_width, block_width, bias, bias_width, directory, combined_blk_dim, append = True, hbm_row_width=64):
    """
    Maps the quantized blocks and bias to two memory files as the fake HBM memory.
    """
    num_blocks_per_row = hbm_row_width // block_width
    num_bias_per_row = hbm_row_width // bias_width

    if not os.path.exists(directory):
        os.makedirs(directory)
    
    if not append:
        # Clear existing files if not appending
        with open(os.path.join(directory, "hbm_ele.mem"), "w") as f:
            f.write("")
        with open(os.path.join(directory, "hbm_scale.mem"), "w") as f:
            f.write("")

    with open(os.path.join(directory, "hbm_ele.mem"), "a") as f:
        insert_block_row = ""
        combined_blk = ""
        index_in_row = 0
        # for i, block in enumerate(reversed(blocks)):
        for i, block in enumerate(blocks):
            combined_blk = combined_blk + map_block_to_value(block, element_width) 
            if i % combined_blk_dim == combined_blk_dim - 1:
                insert_block_row = combined_blk + insert_block_row
                combined_blk = ""
            index_in_row += 1
            if index_in_row == num_blocks_per_row:
                f.write("0x" + insert_block_row + "\n")
                insert_block_row = ""
                index_in_row = 0
        if 0 < index_in_row < num_blocks_per_row:
            # If the last row is not full, pad it with zeros
            insert_block_row = "0" * (num_blocks_per_row - index_in_row) * (element_width // 4) + insert_block_row
            f.write("0x" + insert_block_row + "\n")

    # Save Bias to HBM file            
    with open(os.path.join(directory, "hbm_scale.mem"), "a") as f:
        insert_bias_row = ""
        combined_bias = ""
        index_in_row = 0
        # for i, b in enumerate(reversed(bias)):
        for i, b in enumerate(bias):
            combined_bias = combined_bias + map_scale_to_value(b, bias_width)
            if i % combined_blk_dim == combined_blk_dim - 1:
                insert_bias_row =  combined_bias + insert_bias_row
                combined_bias = ""
            index_in_row += 1
            if index_in_row == num_bias_per_row:
                f.write("0x" + insert_bias_row + "\n")
                insert_bias_row = ""
                index_in_row = 0
        if 0 < index_in_row < num_bias_per_row:
            # If the last row is not full, pad it with zeros
            insert_bias_row = "0" * (num_bias_per_row - index_in_row) * (bias_width // 4) + insert_bias_row
            f.write("0x" + insert_bias_row + "\n")


def map_data_to_fake_hbm_for_behave_sim(blocks, element_width, block_width, bias, bias_width, directory, combined_blk_dim, append = True, hbm_row_width=64):
    """
    Maps the quantized blocks and bias to single memory file fake HBM memory, used as the behavioral simulator input.
    """
    num_blocks_per_row = hbm_row_width // block_width
    num_bias_per_row = hbm_row_width // bias_width

    if not os.path.exists(directory):
        os.makedirs(directory)
    
    if not append:
        # Clear existing files if not appending
        with open(os.path.join(directory, "hbm_for_behave_sim.mem"), "w") as f:
            f.write("")

    with open(os.path.join(directory, "hbm_for_behave_sim.mem"), "a") as f:
        insert_row = ""
        combined_blk = ""
        index_in_row = 0
        for i, block in enumerate(blocks):
            combined_blk = combined_blk + map_block_to_value(block, element_width) 
            if i % combined_blk_dim == combined_blk_dim - 1:
                insert_row = combined_blk + insert_row
                combined_blk = ""
            index_in_row += 1
            if index_in_row == num_blocks_per_row:
                f.write("0x" + insert_row + "\n")
                insert_row = ""
                index_in_row = 0

        combined_bias = ""
        index_ratio = (num_bias_per_row // num_blocks_per_row)
        for i, b in enumerate(bias):
            combined_bias = combined_bias + map_scale_to_value(b, bias_width)
            if i % combined_blk_dim == combined_blk_dim - 1:
                insert_row =  combined_bias + insert_row
                combined_bias = ""
            index_in_row += (1 / index_ratio)
            if index_in_row >= num_bias_per_row:
                f.write("0x" + insert_row + "\n")
                insert_row = ""
                index_in_row = 0
        if 0 < index_in_row < num_blocks_per_row:
            # If the last row is not full, pad it with zeros
            insert_row = "0" * (num_blocks_per_row - int(index_ratio * index_in_row)) * (element_width // 4) + insert_row
            f.write("0x" + insert_row + "\n")



if __name__ == "__main__":
    directory = "../../test/weight"
    fake_hbm_dir = "../../test/load_mem"
    filename = "test_projection_data.pt"
    torch.manual_seed(52)
    quant_config_high = {
        "exp_width": 1,
        "man_width": 2,
        "exp_bias_width": 8,
        "block_size": [1, 4],
        "skip_first_dim": False,
    }
    rand_gen_high = RandomTensorGenerator(
        shape=(16, 8),
        directory=directory,
        filename=filename,
        quant_config=quant_config_high
    )
    
    # Expect shape, blocks.shape = (32, 4), bias.shape = (32, 1)
    rand_gen_high.tensor_gen()
    weight = rand_gen_high.tensor_load()
    blocks, bias = rand_gen_high.quantize_tensor(weight[:8, :])
    map_data_to_fake_hbm_for_rtl_sim(   blocks=blocks,
                            element_width=quant_config_high["exp_width"] + quant_config_high["man_width"] + 1,
                            block_width=(quant_config_high["exp_width"] + quant_config_high["man_width"] + 1) * 4,
                            bias=bias,
                            bias_width=quant_config_high["exp_bias_width"],
                            combined_blk_dim = 2,
                            directory=fake_hbm_dir,
                            append=False,
                            hbm_row_width=256)

    quant_config_low = {
        "exp_width": 4,
        "man_width": 3,
        "exp_bias_width": 8,
        "block_size": [1, 4],
        "skip_first_dim": False,
    }
    rand_gen_low = RandomTensorGenerator(
        shape=(8, 8),
        directory=directory,
        filename=filename,
        quant_config=quant_config_low
    )
    blocks, bias = rand_gen_low.quantize_tensor(weight[8:, :])
    map_data_to_fake_hbm_for_rtl_sim(   blocks=blocks,
                            element_width=quant_config_low["exp_width"] + quant_config_low["man_width"] + 1,
                            block_width=(quant_config_low["exp_width"] + quant_config_low["man_width"] + 1) * 4,
                            bias=bias,
                            bias_width=quant_config_low["exp_bias_width"],
                            combined_blk_dim = 2,
                            directory=fake_hbm_dir,
                            hbm_row_width=256)