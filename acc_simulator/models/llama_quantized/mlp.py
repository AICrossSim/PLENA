from typing import Literal

from torch import Tensor
from transformers.models.llama.modeling_llama import LlamaMLP

from ...quantize.quantized_functions import silu_minifloat
from ...quantize.quantizer.minifloat import MinifloatMeta


class LlamaMLPActFP(LlamaMLP):
    def __init__(
        self, 
        config,
        silu_meta: MinifloatMeta | None,
        silu_func_type: Literal["X", "Xq"] | None,
    ):
        super().__init__(config)
        self.silu_meta = silu_meta
        self.config = config
        self.silu_func_type = silu_func_type


    def forward(self, x: Tensor) -> Tensor:
        x = silu_minifloat(self.gate_proj(x), self.silu_meta, self.silu_func_type) * self.up_proj(x)
        down_proj = self.down_proj(x)
        
        return down_proj
    

    @classmethod
    def from_mlp(
        cls,
        mlp: LlamaMLP,
        silu_meta: MinifloatMeta | None,
        silu_func_type: Literal["X", "Xq"] | None
    ):
        new_mlp = cls(
            config=mlp.config,
            silu_meta=silu_meta,
            silu_func_type=silu_func_type
        )
        device, dtype = next(mlp.parameters()).device, next(mlp.parameters()).dtype
        new_mlp = new_mlp.to(dtype=dtype, device=device)
        new_mlp.load_state_dict(mlp.state_dict(), strict=True)
        return new_mlp
