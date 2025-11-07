# Re-run after kernel reset: Bar plot with three colours by domain, no shaded background.
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Patch

colors = {
    "light_green": tuple(i / 255 for i in (140,107,177)),  # for chatbot
    "turq": tuple(i / 255 for i in (168, 221, 181)),       # for code
    "light_blue": tuple(i / 255 for i in (67, 162, 202))   # for web
}

workload_lib = {
    # --- chatbot (added) ---
    "MT-Bench (LMSYS)":        {"year": 2023, "month": 6,  "domain": "Chatbot",  "tokens_median": 800},
    "AlpacaEval 2.0":          {"year": 2024, "month": 1,  "domain": "Chatbot",  "tokens_median": 700},
    "IFEval":                  {"year": 2023, "month": 10, "domain": "Chatbot",  "tokens_median": 500},
    # --- web/agentic ---
    "WorkArena (HTML)":        {"year": 2024, "month": 6,  "domain": "Web Agent",      "tokens_median": 100_000},
    "BrowserGym (AXTree)":     {"year": 2025, "month": 2,  "domain": "Web Agent",      "tokens_median": 120_000},
    "Computer-Use (full DOM)": {"year": 2025, "month": 5,  "domain": "Web Agent",      "tokens_median": 300_000},
    # --- code ---
    "LiveCodeBench":           {"year": 2024, "month": 10, "domain": "Code Agent",     "tokens_median": 80_000},
    "Multi-SWE-bench":         {"year": 2024, "month": 5,  "domain": "Code Agent",     "tokens_median": 170_000},
    "LongCodeBench":           {"year": 2025, "month": 4,  "domain": "Code Agent",     "tokens_median": 1_000_000},

}

items = [(name, v["domain"], v["tokens_median"], v.get("tokens_p90")) for name, v in workload_lib.items()]
domains_sequence = [v["domain"] for v in workload_lib.values()]
unique_domains = list(dict.fromkeys(domains_sequence))  # preserve order

x_positions = []
labels = []
values = []
upper_err = []
domains_per_bar = []

pos = 0
gap = 0.7
bar_width = 0.8

for dom in unique_domains:
    in_dom = [(n, t50, t90) for (n, d, t50, t90) in items if d == dom]
    for name, t50, t90 in in_dom:
        x_positions.append(pos)
        labels.append(name)
        values.append(t50)
        domains_per_bar.append(dom)
        upper_err.append((t90 - t50) if (t90 is not None and t90 > t50) else 0.0)
        pos += 1
    pos += gap

x = np.array(x_positions)
y = np.array(values)
yerr = np.array([np.zeros_like(y), np.array(upper_err)])

fig, ax = plt.subplots(figsize=(9, 4))

domain_color = {"Web Agent": colors["light_blue"], "Code Agent": colors["turq"], "Chatbot": colors["light_green"]}
bar_colors = [domain_color.get(d, colors["light_blue"]) for d in domains_per_bar]

ax.bar(x, y, width=bar_width, yerr=yerr, capsize=2, error_kw=dict(linewidth=0.8), zorder=2, color=bar_colors)

ax.set_yscale("log")
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=30, ha="right")

ax.set_ylabel("Number of Tokens", labelpad=6)
ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.4)

legend_handles = [Patch(facecolor=domain_color[d], label=d) for d in unique_domains]
ax.legend(handles=legend_handles, ncol=len(unique_domains), fontsize=11, frameon=False, loc="upper left")

def k_formatter(v, _pos):
    if v >= 1_000_000: return f"{int(v/1_000_000)}M"
    if v >= 1_000:     return f"{int(v/1_000)}K"
    return f"{int(v)}"
ax.yaxis.set_major_formatter(FuncFormatter(k_formatter))

for spine in ax.spines.values():
    spine.set_alpha(0.3)

plt.tight_layout()
outfile = "workload_context_by_domain_bar_colors_chatbot.png"
plt.savefig(outfile, dpi=300, bbox_inches="tight", facecolor='white', transparent=False)
