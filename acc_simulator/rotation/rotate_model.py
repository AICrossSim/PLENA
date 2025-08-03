import torch
import tqdm
from typing import Iterable
from .hadamard_utils import apply_exact_had_to_linear, random_hadamard_matrix


def rotate_embeddings(model, Q: torch.Tensor) -> None:
    """
    Mean-center and rotate the input embedding weights using an orthogonal matrix Q.

    Notes:
        - Only supporting Llama.
        - Q should be orthogonal and in float64.
        - Embedding weights are modified in-place and cast to original dtype.
    """
    weight = model.model.embed_tokens.weight
    
    # Mean-center each embedding vector (per token), inplace
    weight_mean = weight.data.mean(dim=-1, keepdim=True)
    weight.data -= weight_mean

    assert Q.shape[0] == Q.shape[1] == weight.shape[1], (
        f"Q must be square and match embedding dim ({weight.shape[1]}), but got {Q.shape}"
    )

    # Rotate
    # Move Q to gpu, on the same device as the weights
    Q = Q.to(weight.device)
    rotated = (weight.data.double() @ Q).to(dtype=weight.dtype)

    weight.data.copy_(rotated)


def rotate_lm_head(model, Q: torch.Tensor) -> None:
    """
    Rotate the LM head weights using an orthogonal matrix Q.
    """
    weight = model.lm_head.weight
    Q = Q.to(weight.device)

    rotated = (weight.data.double() @ Q).to(dtype=weight.dtype)
    weight.data.copy_(rotated)


def rotate_attention_inputs(attn_layer, head_dim, Q: torch.Tensor, online_rotate: bool = True) -> None:
    """
    Rotate the input projection matrices (q_proj, k_proj, v_proj) in the attention layer
    using an orthogonal matrix Q.
    """
    for proj in [attn_layer.q_proj, attn_layer.k_proj, attn_layer.v_proj]:
        weight = proj.weight

        Q = Q.to(weight.device)
        rotated = (weight.data.double() @ Q).to(dtype=weight.dtype)
        weight.data.copy_(rotated)
    
    if online_rotate:
        apply_exact_had_to_linear(attn_layer.v_proj, had_dim=head_dim, output=True)


def rotate_attention_output(attn_layer, Q: torch.Tensor, online_rotate: bool = True) -> None:
    """
    Rotate the out projection matrices (o_proj) in the attention layer
    using an orthogonal matrix Q.T.
    """
    weight = attn_layer.o_proj.weight

    Q = Q.to(weight.device)
    rotated = (Q.T @ weight.data.double()).to(dtype=weight.dtype)
    weight.data.copy_(rotated)

    if online_rotate:
        apply_exact_had_to_linear(attn_layer.o_proj, had_dim=-1, output=False)


def rotate_mlp_input(mlp, Q: torch.Tensor) -> None:
    for ln in [mlp.up_proj, mlp.gate_proj]:
        weight = ln.weight

        Q = Q.to(weight.device)
        rotated = (weight.data.double() @ Q).to(dtype=weight.dtype)
        weight.data.copy_(rotated)


def rotate_mlp_output(mlp, Q: torch.Tensor, online_rotate: bool = True) -> None:
    down_proj = mlp.down_proj
    weight = down_proj.weight

    Q = Q.to(weight.device)
    rotated = (Q.T @ weight.data.double()).to(dtype=weight.dtype)
    weight.data.copy_(rotated)

    if online_rotate:
        # Apply exact (inverse) hadamard on the weights of mlp output, with cuda fht
        # on input feature 
        apply_exact_had_to_linear(down_proj, had_dim=-1, output=False) 


@torch.inference_mode()
def rotate_llama(model, online_rotate = False):
    num_heads = model.config.num_attention_heads
    hidden_dim = model.config.hidden_size
    head_dim = model.config.head_dim
    head_dim = hidden_dim // num_heads

    Q = get_hadamard(hidden_dim, use_fht=False)

    rotate_embeddings(model, Q)
    decoder_layers = model.model.layers
    for _, layer in enumerate(tqdm.tqdm(decoder_layers, unit="LlamaDecoderLayer", desc="Rotating")):
        rotate_attention_inputs(layer.self_attn, head_dim, Q, online_rotate)
        rotate_attention_output(layer.self_attn, Q, online_rotate)
        rotate_mlp_input(layer.mlp, Q)
        rotate_mlp_output(layer.mlp, Q, online_rotate)
    rotate_lm_head(model, Q)


def get_hadamard(size: int, use_fht: bool = False) -> torch.Tensor:
    # Call random hadamard without cuda accelerate (fast-hadamard-transformation)
    if not use_fht:
        # Compute hadamard on cuda 0, later moved to per layer's device for rotation
        device = "cuda:0"
        # Why Random? the auther argued that using random hadamard gives lower ppl
        # While they kept exact hadamard through fht for online rotation for speed.
        # One could read: https://github.com/spcl/QuaRot/issues/11#issuecomment-2079517253
        return random_hadamard_matrix(size, device)
    else:
        # Holder for online exact hadamard
        # TODO
        pass


def fuse_rms_norms(model):
    # Still assume Llama
    decoder_layers = model.model.layers

    for layer in decoder_layers:    
        fuse_ln_linear(layer.input_layernorm, [layer.self_attn.q_proj, layer.self_attn.k_proj, layer.self_attn.v_proj])
        fuse_ln_linear(layer.post_attention_layernorm, [layer.mlp.up_proj, layer.mlp.gate_proj])

    lm_head_norm = model.model.norm
    lm_head = model.lm_head

    fuse_ln_linear(lm_head_norm, [lm_head])


def fuse_ln_linear(layernorm: torch.nn.Module, linear_layers: Iterable[torch.nn.Linear]) -> None:
    """
    Fuse the learnable weights scale and bias from RMSNorm into provided Linear layers.

    The fused Linear has:
        - weight: W_fused = W * gamma
        - bias:   b_fused = b + W @ beta
    """
    for linear in linear_layers:
        weight = linear.weight.data
        dtype = weight.dtype

        # Get scale from layernorm and move to correct device
        gamma = layernorm.weight.data.double().to(weight.device)
        # Fuse scale into weight
        W_fused = (weight.double() * gamma).to(dtype)
        linear.weight.data.copy_(W_fused)

        # Fuse bias (optional)
        if hasattr(layernorm, "bias") and layernorm.bias is not None:
            beta = layernorm.bias.data.double()
            if linear.bias is None:
                linear.bias = torch.nn.Parameter(torch.zeros(linear.out_features, dtype=torch.float64))
            b_fused = (linear.bias.data.double() + weight.double() @ beta).to(dtype)
            linear.bias.data.copy_(b_fused)


def replace_rms_norms(model: torch.nn.Module) -> None:
    """
    Replace all LlamaRMSNorm instances in the model with custom RMSN layers.
    Assumes each RMSNorm has `weight` of shape [hidden_dim].
    """
    from transformers.models.llama.modeling_llama import LlamaRMSNorm

    for name, module in model.named_modules():
        for child_name, child in list(module.named_children()):
            if isinstance(child, LlamaRMSNorm):
                hidden_dim = child.weight.shape[0]
                device = child.weight.device
                # new norm without any learnable weights so no need to copy weights.
                # assume weights pre-fused to linear already.
                new_norm= RMSN(mean_dim=hidden_dim, eps=child.variance_epsilon).to(device)
                new_norm.weight.to(device)
                # Replace the module
                setattr(module, child_name, new_norm)


# Using this non-quantized rmsnorm from qaurot for now
class RMSN(torch.nn.Module):
    """
    This class implements the Root Mean Square Normalization (RMSN) layer.
    We use the implementation from LLAMARMSNorm here:
    https://github.com/huggingface/transformers/blob/main/src/transformers/models/llama/modeling_llama.py#L75
    """

    def __init__(self, mean_dim: int, eps=1e-5):
        super().__init__()
        self.eps = eps
        self.mean_dim = mean_dim
        self.weight = torch.nn.Parameter(torch.zeros(1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        input_dtype = x.dtype
        if x.dtype == torch.float16:
            x = x.to(torch.float32)
        variance = x.pow(2).sum(-1, keepdim=True) / self.mean_dim
        x = x * torch.rsqrt(variance + self.eps)
        return x.to(input_dtype)
