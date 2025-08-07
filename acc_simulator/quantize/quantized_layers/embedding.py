from typing import Literal

import torch
from torch import Tensor, nn

from ..quantizer.mxfp import MXFPMeta, mxfp_quantizer_sim
from ..quantizer.mxint import MXIntMeta, mxint_quantizer_sim
from ..quantizer.minifloat import MinifloatMeta, minifloat_quantizer_sim
from ..utils import quantize_tensor

class MXFPEmbeddingPTQ(nn.Module):
    def __init__(
        self,
        weight: Tensor,
        w_meta: MXFPMeta | MXIntMeta | None,
        layer_type: Literal["W", "Wq"],
    ):
        super().__init__()
        assert weight.ndim == 2, "Expected 2D weight matrix for embedding"

        self.num_embeddings, self.embedding_dim = weight.shape
        self.layer_type = layer_type
        self.w_meta = w_meta

        self.weight = None

        if layer_type == "Wq":
            self.weight = quantize_tensor(weight, block_dim=1, meta=w_meta)
        else:
            self.weight = nn.Parameter(weight, requires_grad=False)


    @torch.no_grad()
    def forward(self, input: Tensor) -> Tensor:
        return torch.nn.functional.embedding(input, self.weight)

    def extra_repr(self) -> str:
        return (
            f"num_embeddings={self.num_embeddings}, embedding_dim={self.embedding_dim}, "
            f"layer_type={self.layer_type}"
            f"w_meta={self.w_meta}"
        )

    @classmethod
    def from_embedding(
        cls,
        layer: nn.Embedding,
        w_meta: MXFPMeta | MXIntMeta | None,
        layer_type: Literal["W", "Wq"],
    ):
        assert isinstance(layer, nn.Embedding), "Expected nn.Embedding instance"
        with torch.no_grad():
            return cls(
                weight=layer.weight.clone(),
                w_meta=w_meta,
                layer_type=layer_type,
            )
