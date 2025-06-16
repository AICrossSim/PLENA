from functools import partial
import torch
import torch.nn as nn

from ..quantizer import minifloat_ieee_quantizer

class RMSNormMINIFP(nn.Module):
    def __init__(self, hidden_size, eps=1e-6, config: dict = None):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.variance_epsilon = eps
        self.config = config or {}
        self.bypass = self.config.get("bypass", False)
        self.is_ptq = self.config.get("is_ptq", False)
        self.weight_requires_quantisation = True if self.is_ptq else False
        self.weight_quantizer = None
        self.input_quantizer = None

        if not self.bypass:
            self._setup_quantizers(self.config)

    def _setup_quantizers(self, config):
        self.input_quantizer = partial(
            minifloat_ieee_quantizer,
            width=config["data_in_width"],
            exponent_width=config["data_in_exponent_width"],
            exponent_bias=config["data_in_exponent_bias_width"],
        )
        self.weight_quantizer = partial(
            minifloat_ieee_quantizer,
            width=config["weight_width"],
            exponent_width=config["weight_exponent_width"],
            exponent_bias=config["weight_exponent_bias_width"],
        )

    def forward(self, hidden_states):
        input_dtype = hidden_states.dtype

        if self.bypass:
            weight = self.weight
            x = hidden_states
        elif self.is_ptq:
            with torch.no_grad():
                x = self.input_quantizer(hidden_states)
                if self.weight_requires_quantisation:
                    self.weight.copy_(self.weight_quantizer(self.weight.data))
                    self.weight_requires_quantisation = False
                weight = self.weight
        else:
            x = self.input_quantizer(hidden_states)
            weight = self.weight_quantizer(self.weight)


        x = x.to(torch.float32)
        variance = x.pow(2).mean(-1, keepdim=True)
        x = x * torch.rsqrt(variance + self.variance_epsilon)
        return (weight * x.to(input_dtype))

    def __repr__(self):
        return "{}(hidden_size={}, bypass={}, is_ptq={}, x/w-width={}/{})".format(
            self.__class__.__name__,
            self.weight.shape[0],
            self.bypass,
            self.is_ptq,
            self.config.get("data_in_width", "NA"),
            self.config.get("weight_width", "NA"),
        )
