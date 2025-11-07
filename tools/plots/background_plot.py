import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

# -------------------------
# Data
# -------------------------
model_lib = {
    "GPT-3":             {"year": 2020, "context_length": 2_048,      "size": 175},
    "GPT-3.5":           {"year": 2022, "context_length": 16_000,     "size": 175},
    # "OPT":               {"year": 2022, "context_length": 2_048,      "size": 175},
    "GPT-4":             {"year": 2023, "context_length": 32_000,     "size": 1000},
    "LLaMA 1":           {"year": 2023, "context_length": 2_048,      "size": 65},
    # "LLaMA 2":           {"year": 2023, "context_length": 4_096,      "size": 70},
    # "LLaMA 3":           {"year": 2024, "context_length": 8_192,      "size": 70},
    # "LLaMA 3.3":         {"year": 2024, "context_length": 128_000,    "size": 70},
    "GPT-5":             {"year": 2025, "context_length": 400_000,    "size": 600},
    "LLaMA4-Maverick":      {"year": 2025, "context_length": 1_000_000, "size": 400},
    "DeepSeek R1":      {"year": 2025, "context_length": 128_000, "size": 671},
    # "Gemini 2.0 Flash":  {"year": 2025, "context_length": 1_000_000, "size": ?},
    # "Claude Opus 4.1":     {"year": 2025, "context_length": 200_000,   "size": 500},
    "Grok 4":            {"year": 2025, "context_length": 256_000,    "size": 1700},
}

# -------------------------
# Preprocess
# -------------------------
items = [(name, v["year"], v["context_length"], v["size"]) for name, v in model_lib.items()]
labels  = [n for n, _, _, _ in items]
years   = np.array([y for _, y, _, _ in items])
ctx     = np.array([c for _, _, c, _ in items], dtype=float)
sizes   = np.array([s for _, _, _, s in items], dtype=float)  # billions of params

# -------------------------
# Plot
# -------------------------
fig, ax = plt.subplots(figsize=(8, 3.5))

# Simple scatter plot without color coding
ax.scatter(sizes, ctx, s=80, c='steelblue', alpha=0.7, 
           edgecolor='white', linewidth=1.5, zorder=3)

# Set both axes to log scale for better visualization
ax.set_xscale("log")
ax.set_yscale("log")

ax.set_xlabel("Model Size (Billion Parameters)", fontsize=12, labelpad=8)
ax.set_ylabel("Context Length (tokens)", fontsize=12, labelpad=8)
# ax.set_title("Model Size vs Context Length", fontsize=12, pad=15)
ax.tick_params(axis='both', which='major', labelsize=12)
ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.4)

# Style the plot
for spine in ax.spines.values():
    spine.set_alpha(0.3)

# Format Y-axis as K/M
def k_formatter(v, _pos):
    if v >= 1_000_000:
        return f"{int(v/1_000_000)}M"
    if v >= 1_000:
        return f"{int(v/1_000)}K"
    return f"{int(v)}"
ax.yaxis.set_major_formatter(FuncFormatter(k_formatter))

# Format X-axis 
def size_formatter(v, _pos):
    if v >= 1000:
        return f"{int(v/1000)}T"  # Trillion parameters
    return f"{int(v)}B"
ax.xaxis.set_major_formatter(FuncFormatter(size_formatter))

# Annotate each point with model name and year
for i, (size, context, name, year) in enumerate(zip(sizes, ctx, labels, years)):
    # Create label with name and year
    label_text = f"{name}\n({year})"
    
    # Smart positioning to avoid overlap
    # Offset based on position to spread labels out
    if size < 100:  # Small models
        xytext = (10, 10)
        ha = 'left'
    elif size > 500:  # Large models
        xytext = (-10, 10)
        ha = 'right'
    else:  # Medium models
        xytext = (0, 15)
        ha = 'center'
    
    # Adjust vertical offset based on context length
    if context > 100_000:
        xytext = (xytext[0], -20)
    
    ax.annotate(
        label_text, (size, context),
        textcoords="offset points",
        xytext=xytext,
        fontsize=10,
        alpha=0.9,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8),
        zorder=5,
        ha=ha,
        va='bottom' if xytext[1] > 0 else 'top'
    )

# Adjust layout
plt.tight_layout()

# Save the plot
plt.savefig("model_size_vs_context_length.png", dpi=300, bbox_inches="tight", 
            facecolor='white', transparent=False)

print("Plot saved successfully!")
# plt.show()