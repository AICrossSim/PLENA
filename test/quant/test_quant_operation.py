
from quant.quant_operations.base import CoarseGrainedQuantOperation, Operation
from quant.quantizer import minifloat_ieee_quantizer
from functools import partial
import torch

def test_minifloat_quantizer():
    a = torch.randn(10, 10)
    b = torch.randn(10, 10)
    quant_func = partial(
        minifloat_ieee_quantizer, 
        width=8, 
        exponent_width=3)
    quant_func_dict = {
        "a": quant_func, 
        "b": quant_func}
    quant_op = CoarseGrainedQuantOperation("add", "minifloat", quant_func_dict)
    base_op = Operation("add")
    print(quant_op(a=a, b=b))
    print(base_op(a=a, b=b))

if __name__ == "__main__":
    test_minifloat_quantizer()