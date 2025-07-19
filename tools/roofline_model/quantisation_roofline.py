import matplotlib.pyplot as plt
import numpy as np
from utils import load_json
from pathlib import Path
import os


turq = (40, 161, 151)
darkblue = (18, 67, 109)
dark_pink = (128, 22, 80)
orange = (244, 106, 37)
turq = tuple([i / 255 for i in turq])
darkblue = tuple([i / 255 for i in darkblue])
dark_pink = tuple([i / 255 for i in dark_pink])
orange = tuple([i / 255 for i in orange])
colors = [darkblue, orange, turq, dark_pink]

# HBM Settings
Operate_Freq = 1e9      # 1 GHz
Batch_Size = 4
MLEN = 128
MLEN_RECT = 512
MLEN_RECT_QUANTISED = 1024
BLEN = 32
DataWidth = 2               # 2 byte per element
Quantised_DataWidth = 0.7   # 4 bits per element
HBM_Bandwidth = 512e9       # 512 GB/s
HBM_Capacity = 128          # 100 GB
SEQ_LENGTH_NORM =  256
SEQ_LENGTH_REASONING = 4096

class RooflineMoel:
    def __init__(self, operate_freq=Operate_Freq, M=MLEN, K=MLEN, data_width=DataWidth, hbm_bandwidth=HBM_Bandwidth, hbm_capacity=HBM_Capacity):
        self.operate_freq = operate_freq
        self.M = M
        self.K = K
        self.data_width = DataWidth
        self.hbm_bandwidth = HBM_Bandwidth
        self.hbm_capacity = HBM_Capacity

    def get_peak_performance(self):
        return self.operate_freq * self.M * self.K * 2
    
    def get_attainable_performance(self, operation_intensity):
        return np.minimum(
            self.get_peak_performance(),
            operation_intensity * self.hbm_bandwidth
        ) / 1e9  # Convert to GFLOPs/s


def hbm_capacity_requirement(
    roofline_model,
    model_config,
    seq_context_length,
    batch_size: int,
    DataWidth
):
    hbm_storage_per_layer = 0
    # Weights and biases per layer
    # QKV Projection Weights & Biases
    hbm_storage_per_layer += model_config.get("hidden_size", 0) * model_config.get("hidden_size", 0) * 3 * DataWidth
    hbm_storage_per_layer += model_config.get("hidden_size", 0) * 3 * DataWidth
    # KV Cache
    hbm_storage_per_layer += seq_context_length * model_config.get("hidden_size", 0) * 2 * batch_size * DataWidth
    # Attention Output
    hbm_storage_per_layer += model_config.get("hidden_size", 0) * seq_context_length * batch_size * DataWidth
    # MLP
    hbm_storage_per_layer += model_config.get("hidden_size", 0) * model_config.get("intermediate_size", 0) * 2 * DataWidth
    hbm_storage_per_layer += model_config.get("intermediate_size", 0) * batch_size * DataWidth
    hbm_storage_per_layer += model_config.get("intermediate_size", 0) * 2 * DataWidth
    hbm_storage_per_layer += model_config.get("hidden_size", 0) * batch_size * DataWidth

    return hbm_storage_per_layer * model_config.get("num_hidden_layers", 0) / 1e9  # Convert to GB

def plot_roofline(ax, roofline_model):
    operation_intensity = np.linspace(0.1, 1000, 1000)  # Avoid log(0)
    performance = roofline_model.get_attainable_performance(operation_intensity)
    ax.plot(operation_intensity, performance, label='Roofline', linewidth=2, color = colors[0])

def fc_square_performance(roofline_model, seq_len, model_config, DataWidth):
    max_batch = 0
    for batch_size in range(1, 128):
        hbm_capacity = hbm_capacity_requirement(roofline_model, model_config, seq_len, batch_size, DataWidth)
        print(f"Batch size: {batch_size}, HBM Capacity: {hbm_capacity} GB")
        if hbm_capacity > roofline_model.hbm_capacity:
            break
        max_batch = batch_size
    print(f"Max batch size for FC Square: {max_batch}")

    achieved_performance = []
    operation_intensity = []
    hbm_capacity_bound = roofline_model.K * roofline_model.operate_freq * max_batch / 1e9
    for batch_size in range(1, roofline_model.K + 1):
        operation_intensity.append(roofline_model.K * roofline_model.operate_freq * batch_size / (roofline_model.K * 2 * 1e9))
        achieved_performance.append(min(roofline_model.K * roofline_model.operate_freq * batch_size / 1e9, operation_intensity[batch_size-1] * roofline_model.hbm_bandwidth / 1e9, hbm_capacity_bound))  # FLOPs/Byte
    return achieved_performance, operation_intensity


def fc_rect_sa_performance(roofline_model, seq_len, model_config, DataWidth):
    max_batch = 0
    for batch_size in range(1, 128):
        hbm_capacity = hbm_capacity_requirement(roofline_model, model_config, seq_len, batch_size, DataWidth)
        if hbm_capacity > roofline_model.hbm_capacity:
            break
        max_batch = batch_size
    print(f"Max batch size for FC Rect SA: {max_batch}")
    achieved_performance = []
    operation_intensity = []
    hbm_capacity_bound = roofline_model.K * roofline_model.operate_freq * max_batch / 1e9
    for batch_size in range(1, MLEN):
        operation_intensity.append(roofline_model.K * roofline_model.operate_freq * batch_size / (roofline_model.K * 2 * 1e9))  # FLOPs/Byte
        achieved_performance.append(min(roofline_model.K * roofline_model.operate_freq * batch_size / 1e9, operation_intensity[batch_size-1] * roofline_model.hbm_bandwidth / 1e9, hbm_capacity_bound))  # GFLOPs
    return achieved_performance, operation_intensity
    



if __name__ == "__main__":
    config_parent_path  = Path(__file__).resolve().parents[2]
    print(f"Config parent path: {config_parent_path}")
    model_config_path   = os.path.join(config_parent_path, "doc/Model_Lib/llama-3.1-70b.json")
    model_config        = load_json(model_config_path)

    rect_roofline_model = RooflineMoel(operate_freq=Operate_Freq, M=BLEN, K=MLEN_RECT, data_width=DataWidth, hbm_bandwidth=HBM_Bandwidth, hbm_capacity=HBM_Capacity)
    # Create side-by-side subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    # --- Left subplot: Square Systolic Array ---
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    ax1.set_xlabel('Operation Intensity (FLOPs/Byte)')
    ax1.set_ylabel('Performance (GFLOPs/s)')
    ax1.set_title('FP16 Systolic Array')
    plot_roofline(ax1, rect_roofline_model)
    achieved_performance, operation_intensity = fc_rect_sa_performance(rect_roofline_model, SEQ_LENGTH_NORM, model_config, DataWidth)
    ax1.plot(operation_intensity, achieved_performance, marker='o',  markersize=4, label='Normal Inference', linestyle='--', color = colors[1])
    achieved_performance, operation_intensity = fc_rect_sa_performance(rect_roofline_model, SEQ_LENGTH_REASONING, model_config, DataWidth)
    ax1.plot(operation_intensity, achieved_performance, marker='o',  markersize=4, label='Reasoning Inference', linestyle='--', color = colors[2])
    ax1.legend()

    # --- Right subplot: Rectangular Systolic Array ---
    quantised_roofline_model = RooflineMoel(operate_freq=Operate_Freq, M=BLEN, K=MLEN_RECT_QUANTISED, data_width=Quantised_DataWidth, hbm_bandwidth=HBM_Bandwidth, hbm_capacity=HBM_Capacity)
    ax2.set_xscale('log')
    ax2.set_yscale('log')
    ax2.set_xticks([1e1, 1e2, 1e3, 1e4, 1e5])
    ax2.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax2.get_xaxis().set_minor_formatter(plt.NullFormatter())
    ax2.set_xlabel('Real Operation Intensity (FLOPs/Byte)')
    ax2.set_ylabel('Performance (GFLOPs/s)')
    ax2.set_title('W4-KV4-A8 Systolic Array')
    ax2.yaxis.set_tick_params(labelleft=True)
    plot_roofline(ax2, quantised_roofline_model)
    achieved_performance, operation_intensity= fc_rect_sa_performance(quantised_roofline_model, SEQ_LENGTH_NORM, model_config, Quantised_DataWidth)
    ax2.plot(operation_intensity, achieved_performance, marker='o', markersize=4, label='Normal Inference', linestyle='--', color = colors[1])
    achieved_performance, operation_intensity= fc_rect_sa_performance(quantised_roofline_model, SEQ_LENGTH_REASONING, model_config, Quantised_DataWidth)
    ax2.plot(operation_intensity, achieved_performance, marker='o', markersize=4, label='Reasoning Inference', linestyle='--', color = colors[2])
    ax2.legend()

    plt.tight_layout()
    plt.savefig('software_optimisation_roofline.png')
    print("Combined plot saved as 'roofline_fc_combined.png'.")
