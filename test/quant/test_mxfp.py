import torch
from quant.quantizer.mxfp import mxfp_quantizer
from quant.quantizer.minifloat import minifloat_ieee_quantizer
from quant.quantizer.utils import _get_similarity


def test_mxfp():
    x = torch.randn(256, 256)* 200 - 100
    mxfp_x = mxfp_quantizer(x, 8, 2, 8, [16])
    minifloat_x = minifloat_ieee_quantizer(x, 8, 2)

    print(_get_similarity(mxfp_x, minifloat_x, metric="L2_norm").mean())
    print(_get_similarity(x, mxfp_x, metric="L2_norm").mean())
    print(_get_similarity(x, minifloat_x, metric="L2_norm").mean())

if __name__ == "__main__":
    test_mxfp()


