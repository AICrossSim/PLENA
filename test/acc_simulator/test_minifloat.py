import sys
import os

import torch
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from acc_simulator.quantize.quantizer.minifloat.minifloat import minifloat_quantizer_sim
from acc_simulator.quantize.quantizer.minifloat.meta import MinifloatMeta

def test_minifloat_quantizer_sim():
    test_tensor = torch.randn(1, 1024, 1024)
    minifloat_meta = MinifloatMeta.from_string("MINIFLOAT_E6M5")
    result = minifloat_quantizer_sim(
        tensor=test_tensor,
        block_dim=None,
        minifloat_meta=minifloat_meta,
    )
    print(result)

if __name__ == "__main__":
    test_minifloat_quantizer_sim()
