from functools import partial

import torch 

from ..quantizer import mxfp_quantizer

# PyTorch has torch.matmul and torch.bmm for matrix multiplication
matmul_mapping = {"matmul": torch.matmul, "bmm": torch.bmm}

def generic_matmul_mxfp(x, y, config, style="matmul"):
    """
    Matrix multiplication with MXPF quantization (block minifloat with compressed exponent bias).
    """
    bypass = config.get("bypass", False)
    matmul = matmul_mapping[style]
    
    if bypass:
        return matmul(x, y)
    else:
        # Extract MXPF quantization config for x
        x_width = config["data_in_width"]
        x_exp_width = config["data_in_exponent_width"]
        x_exp_bias_width = config["data_in_exponent_bias_width"]
        x_block_size = config["data_in_block_size"]
        
        # Extract MXPF quantization config for y
        y_width = config["weight_width"]
        y_exp_width = config["weight_exponent_width"]
        y_exp_bias_width = config["weight_exponent_bias_width"]
        y_block_size = config["weight_block_size"]

        # Whether we are using batched input
        x_is_batched = x.ndim > 2
        y_is_batched = y.ndim > 2

        # Create MXPF-style quantizers
        x_quantizer = partial(
            mxfp_quantizer,
            width=x_width,
            exponent_width=x_exp_width,
            exponent_bias_width=x_exp_bias_width,
            block_size=x_block_size,
            skip_first_dim=x_is_batched,
        )

        y_quantizer = partial(
            mxfp_quantizer,
            width=y_width,
            exponent_width=y_exp_width,
            exponent_bias_width=y_exp_bias_width,
            block_size=y_block_size,
            skip_first_dim=y_is_batched,
        )

        # Flatten for matmul if batched
        x_shape = list(x.shape)
        y_shape = list(y.shape)
        if x_is_batched:
            x = torch.flatten(x, 0, -3)
        if y_is_batched:
            y = torch.flatten(y, 0, -3)

        # Apply quantization
        # The result is still a fp32 tensor, but the values approximate what a true block float would represent.
        x = x_quantizer(x)
        y = y_quantizer(y)

        # Restore shape
        x = x.view(x_shape)
        y = y.view(y_shape)

        return matmul(x, y)

def matmul_mxfp(x, y, config):
    return generic_matmul_mxfp(x, y, config, style="matmul")

def bmm_mxfp(x, y, config):
    return generic_matmul_mxfp(x, y, config, style="bmm")
