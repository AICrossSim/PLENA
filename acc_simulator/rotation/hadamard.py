import torch
from .hadamard_utils import get_hadK, matmul_hadU_cuda
from ..quantize.utils import quantize_tensor


class OnlineHadamardQuantization(torch.nn.Module):
    def __init__(self, hadamard_dim, force_fp32=False, block_dim=-1, meta=None):
        super().__init__()
        self.fp32_had = force_fp32
        had_rem_dim, self.rem_dim = get_hadK(hadamard_dim)
        had_rem_dim_t, self.rem_dim_t = get_hadK(hadamard_dim, transpose=True)
        self.block_dim = block_dim
        self.meta = meta
        if had_rem_dim is not None:
            self.register_buffer("had_rem_dim", had_rem_dim)
            self.register_buffer("had_rem_dim_t", had_rem_dim_t)
            if not self.fp32_had:
                self.had_rem_dim = self.had_rem_dim.to(torch.float16)
                self.had_rem_dim_t = self.had_rem_dim_t.to(torch.float16)
        else:
            self.had_rem_dim = None
            self.had_rem_dim_t = None
    
    def forward(self, x):
        x_dtype = x.dtype
        if self.fp32_had:
            x = x.float()
        x = matmul_hadU_cuda(x, self.had_rem_dim, self.rem_dim)
        x = quantize_tensor(x, block_dim=self.block_dim, meta=self.meta)
        x = matmul_hadU_cuda(x, self.had_rem_dim_t, self.rem_dim_t)
        x = x.to(x_dtype)
        return x
