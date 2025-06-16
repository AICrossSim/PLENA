from quant.quantizer.hardware_quantizer import pack_fp_to_bin, _mx_fp_quantize_hardware, _minifloat_ieee_quantize_hardware
import torch
from cfl_tools.debugger import set_excepthook
from cfl_tools.logger import set_logging_verbosity, get_logger

logger = get_logger("test_bin_mxfp")
set_logging_verbosity("debug")
set_excepthook()


if __name__ == "__main__":
    torch.manual_seed(0)
    weight = torch.randn(6,6)
    quant_config = {
        "exp_width": 8,
        "man_width": 8,
        "exp_bias_width": 8,
        "block_size": [2, 2],
        "skip_first_dim": False,
    }
    quant_weight, per_block_quant_weight, per_block_exponent_bias = _mx_fp_quantize_hardware(
        weight,
        width = quant_config["exp_width"] + quant_config["man_width"] + 1,
        exponent_width = quant_config["exp_width"],
        exponent_bias_width = quant_config["exp_bias_width"],
        block_size = quant_config["block_size"],
        skip_first_dim = quant_config["skip_first_dim"],
    )
    logger.debug(f"quant_weight: {quant_weight.shape}")
    logger.debug(f"per_block_quant_weight: {per_block_quant_weight.shape}")
    logger.debug(f"per_block_exponent_bias: {per_block_exponent_bias.shape}")

    per_block_quant_weight = per_block_quant_weight.transpose(-2, -1)
    per_block_exponent_bias = per_block_exponent_bias.transpose(-2, -1)


    weight_list = []
    for i in range(per_block_quant_weight.shape[0]):
        quant_weight, exponent, mantissa = _minifloat_ieee_quantize_hardware(
            per_block_quant_weight[i],
            width = quant_config["exp_width"] + quant_config["man_width"] + 1,
            exponent_width = quant_config["exp_width"],
            exponent_bias = per_block_exponent_bias[i],
        )
        bin_block = pack_fp_to_bin(
            exponent,
            mantissa,
            quant_config["exp_width"],
            quant_config["man_width"],
        )
        weight_list.append((bin_block.tolist(), int(per_block_exponent_bias[i])))
        # note here the block_mantissa was represented as unsigned integer
        # the exponent was represented as signed integer

    logger.debug(f"weight_list: {weight_list}")
