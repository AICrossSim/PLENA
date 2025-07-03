from quant.quantizer import _mx_fp_quantize
import torch

def random_mx_fp_generator(
    Num: int = 10,
    width: int = 8,
    exponent_width: int = 3,
    exponent_bias_width: int = 3,
    block_size: list[int] | int = [16],
    skip_first_dim: bool = False,
):
    fp_random = torch.randn(Num, dtype=torch.float32)
    print(f"Generated random tensor: {fp_random}")
    mx_fp_random = _mx_fp_quantize(
        fp_random,
        width=width,
        exponent_width=exponent_width,
        exponent_bias_width=exponent_bias_width,
        block_size=block_size,
        skip_first_dim=skip_first_dim,
    )
    return mx_fp_random



if __name__ == "__main__":
    # Example usage
    random_mx_fp = random_mx_fp_generator(
        Num=10,
        width=8,
        exponent_width=3,
        exponent_bias_width=16,
        block_size=[8],
        skip_first_dim=False
    )
    print(random_mx_fp)