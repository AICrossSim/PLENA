from functools import partial
import torch
import torch.nn as nn
import torch.nn.functional as F

from ..quantizer import mxfp_quantizer

class EmbeddingMXFP(nn.Embedding):
    def __init__(
        self,
        num_embeddings: int,
        embedding_dim: int,
        padding_idx: int = None,
        config: dict = None,
        device=None,
        dtype=None,
    ):
        super().__init__(num_embeddings, embedding_dim, padding_idx=padding_idx, device=device, dtype=dtype)

        self.config = config
        self.bypass = config.get("bypass", False)
        self.is_inference = config.get("is_ptq", False)
        self.weight_requires_quantisation = True if self.is_inference else False

        if not self.bypass:
            self._setup_quantizer(config)

    def _setup_quantizer(self, config: dict):
        self.w_quantizer = partial(
            mxfp_quantizer,
            width=config["weight_width"],
            exponent_width=config["weight_exponent_width"],
            exponent_bias_width=config["weight_exponent_bias_width"],
            block_size=config["weight_block_size"],
            skip_first_dim=False,  # do not skip dim 0 — quantize over [num_embeddings, emb_dim]
        )

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        if self.bypass:
            return F.embedding(input, self.weight, self.padding_idx)
        else:
            with torch.no_grad():
                if self.weight_requires_quantisation:
                    self.weight.copy_(self.w_quantizer(self.weight.data))
                    self.weight_requires_quantisation = False
            return F.embedding(input, self.weight, self.padding_idx)


    def __repr__(self):
        txt = "{}(num_embeddings={}, embedding_dim={}, padding_idx={}, bypass={}, is_ptq={}, weight-width={})".format(
            self.__class__.__name__,
            self.num_embeddings,
            self.embedding_dim,
            self.padding_idx,
            self.bypass,
            self.is_ptq,
            self.config["weight_width"],
        )
        return txt
