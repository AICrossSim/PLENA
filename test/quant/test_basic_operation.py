
from quant.quant_operations.base import Operation
import torch

if __name__ == "__main__":
    a = torch.randn(10, 10)
    b = torch.randn(10, 10)
    op = Operation("add")
    print(op(a, b))
    op = Operation("mul")
    print(op(a=a, b=b))
    op = Operation("matmul")
    print(op(a, b=b))
