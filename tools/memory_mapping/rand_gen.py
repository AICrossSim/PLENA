from quant.quantizer.hardware_quantizer import _mx_fp_quantize_hardware, _minifloat_ieee_quantize_hardware
from cfl_cocotb.torch_fp_conversion import pack_fp_to_bin
import torch
import os
from cfl_tools.debugger import set_excepthook
from cfl_tools.logger import set_logging_verbosity, get_logger

logger = get_logger("test_bin_mxfp")
set_logging_verbosity("debug")
set_excepthook()

class Random_MXFP_Tensor_Generator:
    def __init__(self, shape, quant_config, directory=None, filename=None):
        """
        Initialize the random tensor generator with a given shape in MXFP.
        If directory and filename are provided, the tensor will be saved to a file.
        """
        self.shape          = shape
        self.directory      = directory
        self.filename       = filename
        self.quant_config   = quant_config

    def tensor_gen(self):
        tensor = torch.randn(self.shape)
        if self.directory and self.filename:
            if not os.path.exists(self.directory):
                os.makedirs(self.directory)
            file_path = os.path.join(self.directory, self.filename)
            torch.save(tensor, file_path)
            logger.debug(f"Tensor saved to {file_path}")
    
    def tensor_load(self):
        if self.directory and self.filename:
            file_path = os.path.join(self.directory, self.filename)
            if os.path.exists(file_path):
                tensor = torch.load(file_path)
                logger.debug(f"Tensor loaded from {file_path}")
                return tensor
            else:
                logger.error(f"File {file_path} does not exist.")
                return None
        else:
            logger.error("Directory and filename must be specified to load the tensor.")
            return None

    def quantize_tensor(self, tensor):
        '''
        note in 2d case the tensor of the original shape [shape_1, shape_2]
        the output bm_x will keep the orignal shape
        but the per_block * will be packed as showns
        [shape_1 * shaped_2 // (block_size[0] * block_size[1]), block_size[0] * block_size[1]]
        '''
        bm_x, per_block_exponent, per_block_mantissa, per_block_scaling = _mx_fp_quantize_hardware(
            tensor,
            width               = self.quant_config["exp_width"] + self.quant_config["man_width"] + 1,
            exponent_width      = self.quant_config["exp_width"],
            exponent_bias_width = self.quant_config["exp_bias_width"],
            block_size          = self.quant_config["block_size"],
            skip_first_dim      = self.quant_config["skip_first_dim"],
        )

        logger.debug(f"per_block_mantissa: {per_block_mantissa.shape}")
        logger.debug(f"per_block_exponent: {per_block_exponent.shape}")
        logger.debug(f"per_block_quant_bias: {per_block_scaling.shape}")

        block_list  = []
        scaling_list   = []

        for i in range(per_block_mantissa.shape[0]):
            bin_block = pack_fp_to_bin(
                per_block_exponent[i],
                per_block_mantissa[i],
                self.quant_config["exp_width"],
                self.quant_config["man_width"],
            )
            block_list.append(bin_block.tolist())
            scaling_list.append(int(per_block_scaling[i]))
            # note here the block_mantissa was represented as unsigned integer
            # the exponent was represented as signed integer
        logger.debug(f"block_list: {block_list}")
        logger.debug(f"scaling_list: {scaling_list}")

        return block_list, scaling_list


class Random_MXINT_Tensor_Generator:
    def __init__(self, shape, quant_config, directory=None, filename=None):
        """
        Initialize the random tensor generator with a given shape in MXFP.
        If directory and filename are provided, the tensor will be saved to a file.
        """
        self.shape          = shape
        self.directory      = directory
        self.filename       = filename
        self.quant_config   = quant_config

    def tensor_gen(self):
        tensor = torch.randn(self.shape)
        if self.directory and self.filename:
            if not os.path.exists(self.directory):
                os.makedirs(self.directory)
            file_path = os.path.join(self.directory, self.filename)
            torch.save(tensor, file_path)
            logger.debug(f"Tensor saved to {file_path}")
    
    def tensor_load(self):
        if self.directory and self.filename:
            file_path = os.path.join(self.directory, self.filename)
            if os.path.exists(file_path):
                tensor = torch.load(file_path)
                logger.debug(f"Tensor loaded from {file_path}")
                return tensor
            else:
                logger.error(f"File {file_path} does not exist.")
                return None
        else:
            logger.error("Directory and filename must be specified to load the tensor.")
            return None

    def quantize_tensor(self, tensor):
        '''
        note in 2d case the tensor of the original shape [shape_1, shape_2]
        the output bm_x will keep the orignal shape
        but the per_block * will be packed as showns
        [shape_1 * shaped_2 // (block_size[0] * block_size[1]), block_size[0] * block_size[1]]
        '''
        bm_x, per_block_exponent, per_block_mantissa, per_block_scaling = _mx_fp_quantize_hardware(
            tensor,
            width               = self.quant_config["exp_width"] + self.quant_config["man_width"] + 1,
            exponent_width      = self.quant_config["exp_width"],
            exponent_bias_width = self.quant_config["exp_bias_width"],
            block_size          = self.quant_config["block_size"],
            skip_first_dim      = self.quant_config["skip_first_dim"],
        )

        logger.debug(f"per_block_mantissa: {per_block_mantissa.shape}")
        logger.debug(f"per_block_exponent: {per_block_exponent.shape}")
        logger.debug(f"per_block_quant_bias: {per_block_scaling.shape}")

        block_list  = []
        scaling_list   = []

        for i in range(per_block_mantissa.shape[0]):
            bin_block = pack_fp_to_bin(
                per_block_exponent[i],
                per_block_mantissa[i],
                self.quant_config["exp_width"],
                self.quant_config["man_width"],
            )
            block_list.append(bin_block.tolist())
            scaling_list.append(int(per_block_scaling[i]))
            # note here the block_mantissa was represented as unsigned integer
            # the exponent was represented as signed integer
        logger.debug(f"block_list: {block_list}")
        logger.debug(f"scaling_list: {scaling_list}")

        return block_list, scaling_list


class Random_MXFP_Tensor_Generator:
    def __init__(self, shape, quant_config, directory=None, filename=None):
        """
        Initialize the random tensor generator with a given shape.
        If directory and filename are provided, the tensor will be saved to a file.
        """
        self.shape          = shape
        self.directory      = directory
        self.filename       = filename
        self.quant_config   = quant_config

    def tensor_gen(self):
        tensor = torch.randn(self.shape)
        if self.directory and self.filename:
            if not os.path.exists(self.directory):
                os.makedirs(self.directory)
            file_path = os.path.join(self.directory, self.filename)
            torch.save(tensor, file_path)
            logger.debug(f"Tensor saved to {file_path}")
    
    def tensor_load(self):
        if self.directory and self.filename:
            file_path = os.path.join(self.directory, self.filename)
            if os.path.exists(file_path):
                tensor = torch.load(file_path)
                logger.debug(f"Tensor loaded from {file_path}")
                return tensor
            else:
                logger.error(f"File {file_path} does not exist.")
                return None
        else:
            logger.error("Directory and filename must be specified to load the tensor.")
            return None


if __name__ == "__main__":
    pass