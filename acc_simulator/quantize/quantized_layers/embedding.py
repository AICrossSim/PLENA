from typing import Literal

import torch
from torch import Tensor, nn

from mase_triton.mxfp.functional import quantize_dequantize as mxfp_quantizer_sim
from ..quantizer.mxfp import MXFPMeta

class MXFPEmbeddingPTQ(nn.Module):
    def __init__(
        self,
        weight: Tensor,
        w_mxfp_meta: MXFPMeta | None,
        layer_type: Literal["W", "Wq"],
    ):
        super().__init__()
        assert weight.ndim == 2, "Expected 2D weight matrix for embedding"

        self.num_embeddings, self.embedding_dim = weight.shape
        self.layer_type = layer_type
        self.w_mxfp_meta = w_mxfp_meta

        self.weight = None

        if layer_type == "Wq":
            self.weight = mxfp_quantizer_sim(weight, block_dim=1, mxfp_meta=w_mxfp_meta)
        else:
            self.weight = nn.Parameter(weight, requires_grad=False)


    @torch.no_grad()
    def forward(self, input: Tensor) -> Tensor:
        return torch.nn.functional.embedding(input, self.weight)

    def extra_repr(self) -> str:
        return (
            f"num_embeddings={self.num_embeddings}, embedding_dim={self.embedding_dim}, "
            f"layer_type={self.layer_type}"
            f"w_mxfp_meta={self.w_mxfp_meta}"
        )

    @classmethod
    def from_embedding(
        cls,
        layer: nn.Embedding,
        w_mxfp_meta: MXFPMeta | None,
        layer_type: Literal["W", "Wq"],
    ):
        assert isinstance(layer, nn.Embedding), "Expected nn.Embedding instance"
        with torch.no_grad():
            return cls(
                weight=layer.weight.clone(),
                w_mxfp_meta=w_mxfp_meta,
                layer_type=layer_type,
            )
