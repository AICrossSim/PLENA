import torch
from cfl_tools.logger import get_logger

logger = get_logger(__name__)

def fp_mult_hardware(
        exp_a: torch.Tensor,
        mant_a: torch.Tensor,
        exp_b: torch.Tensor,
        mant_b: torch.Tensor,
        IN_FIX_FRAC_WIDTH: int,
        OUT_FIX_FRAC_WIDTH: int,
        log,
):
    exp_out = exp_a + exp_b
    intermediate_mant = mant_a * mant_b
    mant_out = (intermediate_mant * 2**(OUT_FIX_FRAC_WIDTH)).floor()
    log.debug(f"software mant_out: {mant_out}")
    mant_out = mant_out / 2**(OUT_FIX_FRAC_WIDTH)

    return exp_out, mant_out

def test_fp_mult_hardware():
    exp_a = torch.tensor([1, 2, 3, 4])
    mant_a = torch.tensor([1, 2, 3, 4])
    exp_b = torch.tensor([1, 2, 3, 4])
    mant_b = torch.tensor([1, 2, 3, 4])
    IN_FIX_FRAC_WIDTH = 4
    OUT_FIX_FRAC_WIDTH = 4
    log = get_logger(__name__)
    exp_out, mant_out = fp_mult_hardware(exp_a, mant_a, exp_b, mant_b, IN_FIX_FRAC_WIDTH, OUT_FIX_FRAC_WIDTH, log)
    print(exp_out, mant_out)