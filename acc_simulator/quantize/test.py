from typing import Literal

import torch
from torch import Tensor, nn

from quantizer.mxint import MXIntMeta, extract_mxint_components, mxint_quantizer_sim

def test_extract_mxint_components():
    data = torch.randn(1024).to("cuda").bfloat16()
    meta = MXIntMeta.from_string("MXINT_8_B32_S8")
    scale, elements = extract_mxint_components(data, mxint_meta=meta)
    bias = 127
    print(scale.shape)
    print((elements/2**7) * 2**(scale - bias))
    print(data)
    # print(elements.shape)


def test_mxint_quantizer_sim():
    torch.manual_seed(0)
    data = torch.randn(32).bfloat16().to("cuda")
    meta = MXIntMeta.from_string("MXINT_4_B16_S8")
    dq = mxint_quantizer_sim(data, block_dim=0, mxint_meta=meta)
    print(dq)
    print(data)

if __name__ == "__main__":
    test_mxint_quantizer_sim()
