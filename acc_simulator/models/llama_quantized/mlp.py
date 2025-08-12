from typing import Literal

from torch import Tensor
import torch
from transformers.models.llama.modeling_llama import LlamaMLP

from ...quantize.quantized_functions import silu_minifloat
from ...quantize.quantizer.minifloat import MinifloatMeta
from ...rotation import matmul_hadU_cuda, get_hadK, OnlineHadamardQuantization


class LlamaMLPActFP(LlamaMLP):
    def __init__(
        self, 
        config,
        silu_meta: MinifloatMeta | None,
        silu_func_type: Literal["X", "Xq"] | None,
        online_rotate: bool
    ):
        super().__init__(config)
        self.silu_meta = silu_meta
        self.config = config
        self.silu_func_type = silu_func_type
        self.online_rotate = online_rotate


    def forward(self, x: Tensor) -> Tensor:
        x = silu_minifloat(self.gate_proj(x), self.silu_meta, self.silu_func_type) * self.up_proj(x)
        
        # plot_activation_distribution(x, title="Before Hadamard", step=0, save_path="before_hadamard")

        # rotate activation on-line here, before down_projection after nonlinear
        # if self.online_rotate:
        #     x_dtype = x.dtype
        #     had_K, K = get_hadK(self.config.intermediate_size)
        #     had_K_t, K_t = get_hadK(self.config.intermediate_size, transpose=True)
        #     x = matmul_hadU_cuda(x, had_K, K).to(x_dtype)
        #     x = matmul_hadU_cuda(x, had_K_t, K_t).to(x_dtype)
        #     plot_activation_distribution(x, title="After Hadamard", step=0, save_path="after_hadamard")
        
        down_proj = self.down_proj(x)
        
        return down_proj
    

    @classmethod
    def from_mlp(
        cls,
        mlp: LlamaMLP,
        silu_meta: MinifloatMeta | None,
        silu_func_type: Literal["X", "Xq"] | None,
        online_rotate: bool
    ):
        new_mlp = cls(
            config=mlp.config,
            silu_meta=silu_meta,
            silu_func_type=silu_func_type,
            online_rotate=online_rotate
        )
        device, dtype = next(mlp.parameters()).device, next(mlp.parameters()).dtype
        new_mlp = new_mlp.to(dtype=dtype, device=device)
        new_mlp.load_state_dict(mlp.state_dict(), strict=True)
        return new_mlp
