import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ----------------------
# Tunable parameters
# ----------------------
B  = 1       # batch size
H  = 32      # number of heads
d  = 128     # head dimension
s  = 2       # bytes per element (e.g., 2 for FP16/BF16, 1 for INT8, 4 for FP32)

L_min = 512
L_max = 128000
num_points = 40  # number of sample points across [L_min, L_max]

# Generate context lengths (log-spaced)
L_values = np.unique(np.logspace(np.log10(L_min), np.log10(L_max), num=num_points, base=10).astype(int))

def bytes_per_token_fa(L, B, H, d, s):
    return s * B * H * (2*L*d + 2*d)

def bytes_per_token_baseline(L, B, H, d, s):
    return s * B * H * (4*L*d + 4*L + 2*d)

fa_bytes   = np.array([bytes_per_token_fa(L, B, H, d, s) for L in L_values], dtype=np.float64)
base_bytes = np.array([bytes_per_token_baseline(L, B, H, d, s) for L in L_values], dtype=np.float64)

# Convert bytes to GB for readability
to_GB = 1.0 / (1024**3)
fa_gb = fa_bytes * to_GB
print("fa_gb :", fa_gb)

base_gb = base_bytes * to_GB
print("base_gb :", base_gb)

# Plot: Bytes/Token vs Context Length (single plot)
plt.figure(figsize=(7, 5), dpi=140)
plt.plot(L_values, base_gb, label="Baseline", linewidth=2)
plt.plot(L_values, fa_gb,   label="FA-native", linewidth=2)
plt.xscale("log")
plt.yscale("log")
plt.xlabel("Context length L (tokens)")
plt.ylabel("Bytes per token (GB)")
plt.title("Decoding: DRAM Traffic per Token vs Context Length\n(Your formulas)")
plt.legend()
plt.grid(True, which="both", linewidth=0.5, alpha=0.6)


plt.tight_layout()
plt.savefig("decode_bytes_per_token_your_formulas.png", bbox_inches="tight", transparent=True, dpi=300)