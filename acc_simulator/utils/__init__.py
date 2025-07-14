from .set_quant_args import setup_args_linear_nonlinear
from .set_quant_args_cc import setup_args_linear_nonlinear_cc
from .replace_modules import replace_modules
from .load_model import create_device_map

__all__ = ["setup_args_linear_nonlinear", "setup_args_linear_nonlinear_cc", "replace_modules", "create_device_map"]