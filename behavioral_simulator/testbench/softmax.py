import torch
import torch.nn.functional as F


def softmax_max_method(logits):
    # Method 1: apply softmax then take the max probability
    x0 = torch.argmax(logits, dim=-1)
    p = F.softmax(logits.to(torch.float64), dim=-1)
    x0_p = torch.gather(p, dim=-1, index=x0.unsqueeze(-1)).squeeze(-1)
    #p = torch.softmax(logits, dim=-1)
    #return p.max(dim=-1).values  # (B, L)
    return x0_p

def stable_max_method(logits):
    # Method 2: numerically stable via max-logit; no explicit softmax
    m = logits.max(dim=-1).values                 # (B, L)
    exp_shifted = torch.exp(logits - m.unsqueeze(-1))  # (B, L, V)
    denom = exp_shifted.sum(dim=-1)               # (B, L)
    return 1.0 / denom                            # (B, L)

# Test
torch.manual_seed(0)
B, L, V = 3, 5, 10
logits = torch.randn(B, L, V, dtype=torch.float64)

result_softmax = softmax_max_method(logits)
result_stable = stable_max_method(logits)

print("Softmax→max result:\n", result_softmax)
print("Stable formula result:\n", result_stable)
print("\nAre they equal (allclose)?", torch.allclose(result_softmax, result_stable, atol=1e-12))
