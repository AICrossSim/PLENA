import torch
from torch import Tensor

from .meta import MinifloatMeta
from .torch_minifloat import minifloat_denorm_quantizer, minifloat_ieee_quantizer, minifloat_quantizer

def extract_minifloat_component(x: Tensor, minifloat_meta: MinifloatMeta) -> Tensor:
    exp_bits = minifloat_meta.element_exp_bits
    frac_bits = minifloat_meta.element_frac_bits
    total_bits = exp_bits + frac_bits + 1

    return minifloat_quantizer(x, total_bits, exp_bits)

def compose_minifloat_component(x: Tensor, minifloat_meta: MinifloatMeta, output_dtype: torch.dtype) -> Tensor:
    return x.to(output_dtype)

