import matplotlib.pyplot as plt
import numpy as np
from utils import load_json
from pathlib import Path
import os

# HBM Settings
Operate_Freq = 1e9  # 1 GHz
Batch_Size = 4
MLEN = 128
BLEN = 16
DataWidth = 1 # 1 byte per element
HBM_Bandwidth = 460e9  # 460 GB/s
HBM_Capacity = 100e9  # 100 GB
seq_context_length = 2048

class RooflineMoel:
    def __init__(self):
        self.operate_freq = Operate_Freq
        self.M = MLEN
        self.K = MLEN
        self.N = MLEN
        self.data_width = DataWidth
        self.hbm_bandwidth = HBM_Bandwidth
        self.hbm_capacity = HBM_Capacity

    def get_peak_performance(self):
        return self.operate_freq * self.M * self.K * self.data_width
    
    def get_attainable_performance(self, operation_intensity):
        return np.minimum(
            self.get_peak_performance(),
            operation_intensity * self.hbm_bandwidth
        ) / 1e9  # Convert to GFLOPs/s



def hbm_capacity_requirement(
    roofline_model,
    model_config,
    batch_size: int
):
    hbm_storage_per_layer = 0
    # Weights and biases per layer
    # QKV Projection Weights & Biases
    hbm_storage_per_layer += model_config.get("hidden_size", 0) * model_config.get("hidden_size", 0) * 3
    hbm_storage_per_layer += model_config.get("hidden_size", 0) * 3
    # KV Cache
    hbm_storage_per_layer += seq_context_length * model_config.get("hidden_size", 0) * 2 * batch_size
    # Attention Output
    hbm_storage_per_layer += model_config.get("hidden_size", 0) * seq_context_length * batch_size
    # MLP
    hbm_storage_per_layer += model_config.get("hidden_size", 0) * model_config.get("intermediate_size", 0) * 2  # Weights
    hbm_storage_per_layer += model_config.get("intermediate_size", 0) * batch_size  # activation
    hbm_storage_per_layer += model_config.get("intermediate_size", 0) * 2
    hbm_storage_per_layer += model_config.get("hidden_size", 0) * batch_size  # activation

    return hbm_storage_per_layer * model_config.get("num_hidden_layers", 0) / 1e9  # Convert to GB


def plot_roofline(ax, roofline_model):
    operation_intensity = np.linspace(0.1, 1000, 1000)  # Avoid log(0)
    performance = roofline_model.get_attainable_performance(operation_intensity)
    ax.plot(operation_intensity, performance, label='Roofline', linewidth=2)
    ax.axhline(roofline_model.get_peak_performance() / 1e9, color='r', linestyle='--', label='Peak Performance')


def FC_attainable_performance(ax, roofline_model, model_config):
    max_batch = 0
    for batch_size in range(1, 16):
        hbm_capacity = hbm_capacity_requirement(roofline_model, model_config, batch_size)
        if hbm_capacity > roofline_model.hbm_capacity:
            break
        max_batch = batch_size

    achieved_performance = []
    operation_intensity = []
    for batch_size in range(1, max_batch + 1):
        achieved_performance.append(roofline_model.K * roofline_model.operate_freq * batch_size / 1e9)  # GFLOPs
        operation_intensity.append(roofline_model.K * roofline_model.operate_freq * batch_size / (roofline_model.K * 2 * 1e9))  # FLOPs/Byte

    ax.plot(operation_intensity, achieved_performance, marker='o', label='FC Achieved', linestyle='--')



if __name__ == "__main__":
    config_parent_path = Path(__file__).resolve().parents[2]
    print(f"Config parent path: {config_parent_path}")
    model_config_path = os.path.join(config_parent_path, "doc/Model_Lib/llama-3.1-8b.json")
    model_config = load_json(model_config_path)
    roofline_model = RooflineMoel()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Operation Intensity (FLOPs/Byte)')
    ax.set_ylabel('Performance (GFLOPs/s)')
    ax.set_title('Roofline vs FC Attainable Performance')

    plot_roofline(ax, roofline_model)
    FC_attainable_performance(ax, roofline_model, model_config)

    ax.legend()
    ax.grid(True, which='both', linestyle='--')
    plt.tight_layout()
    plt.savefig('square_shape_roofline_fc.png')
