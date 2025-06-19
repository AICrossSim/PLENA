import torch
from torch import Tensor

from quant.quantizer.utils import block, my_clamp, unblock, my_round
from quant.quantizer.hardware_quantizer.minifloat import _minifloat_ieee_quantize_hardware

def _mx_fp_quantize_hardware(
    x: Tensor,
    width: int,
    exponent_width: int,
    exponent_bias_width: int,
    block_size: list[int] | int = [16],
    skip_first_dim: bool = False,
):
    """
    - Convert IEEE FP32/64 to Block Minifloat (BM) which is also called as MXFP, where an exponent bias is shared over all elements in a block
    - `2**-bias_shared x [(-1)^s1 x 2^exponent1 x mantissa1, (-1)^s2 x 2^exponent2 x mantissa2, ...]`
    - See https://openreview.net/forum?id=6zaTwpNSsQ2

    ---
    - forward: convert IEEE FP32/64 to BM
    - backward: STE

    ---
    - `width`: the number of bits (1 sign bit + exponent_bits + mantissa_bits)
    - `exponent_width`: the number of exponent_bits
    - `exponent_bias_width`: the number of bits of the shared exponent bias
    - `block_size`: a list of integers where each integer is the block size on that dimension. See function `block`.

    """

    x_shape_before_blocking = [i for i in x.shape]
    blocked_x, per_block_max, padded_x_shape, block_shape = block(
        x, block_shape=block_size, skip_first_dim=skip_first_dim
    )

    # fill zeros to avoid log2(0) = -inf
    if torch.all(per_block_max == 0):
        per_block_max = torch.ones_like(per_block_max)
    else:
        per_block_max[per_block_max == 0] = per_block_max[per_block_max != 0].min()

    per_block_exponent_bias = my_clamp(
        torch.floor(torch.log2(per_block_max)), 0, 2**exponent_bias_width - 1
    )

    blocked_x = blocked_x / 2**per_block_exponent_bias
    _minifloat_ieee_quantize_hardware(torch.tensor([1.5]), 4,3)

    per_block_bm_x, per_block_fp_exp, per_block_fp_mant = _minifloat_ieee_quantize_hardware(
        blocked_x,
        width=width,
        exponent_width=exponent_width,
    )
    
    per_block_bm_x = per_block_fp_exp * 2**per_block_exponent_bias

    bm_x = unblock(
        per_block_bm_x,
        x_shape_before_blocking=x_shape_before_blocking,
        padded_x_shape=padded_x_shape,
        block_shape=block_shape,
        skipped_first_dim_when_blocking=skip_first_dim,
    )
    fp_exp = unblock(
        per_block_fp_exp,
        x_shape_before_blocking=x_shape_before_blocking,
        padded_x_shape=padded_x_shape,
        block_shape=block_shape,
        skipped_first_dim_when_blocking=skip_first_dim,
    )
    fp_mant = unblock(
        per_block_fp_mant,
        x_shape_before_blocking=x_shape_before_blocking,
        padded_x_shape=padded_x_shape,
        block_shape=block_shape,
        skipped_first_dim_when_blocking=skip_first_dim,
    )
    return bm_x, fp_exp, fp_mant, per_block_exponent_bias

if __name__ == "__main__":
    x = torch.tensor([0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0])
    exp_bias_width = 4
    exp_width = 4
    mant_width = 3
    width = exp_width + mant_width + 1
    bm_x, fp_exp, fp_mant, per_block_exponent_bias = _mx_fp_quantize_hardware(
        x, width, exp_width, exp_bias_width, [2]
    )
    print(bm_x)
    print(fp_exp)
    print(fp_mant)
    print(per_block_exponent_bias)

    from quant.quantizer.hardware_quantizer.utils import pack_fp_to_bin
    fp_bin = pack_fp_to_bin(fp_exp, fp_mant, exp_width, mant_width)
    print(fp_bin)
