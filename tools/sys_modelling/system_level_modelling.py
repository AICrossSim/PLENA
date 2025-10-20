import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from utils import load_json
from pathlib import Path
import os

# HBM Settings
Operate_Freq = 1e9      # 1 GHz
DataWidth = 2           
HBM_Bandwidth = 512     # 800 GB/s
HBM_Capacity = 144      # 128 GB
SEQ_LENGTH_NORM =  5000
SEQ_LENGTH_REASONING = 6500

PLENA_with_3D_STACKED_SRAM = {
    "HBM_Capacity": HBM_Capacity,  # HBM 3e
    "HBM_Bandwidth": HBM_Bandwidth,  # 512 GB/s
    "Operate_Freq": 1e9,  # 1 GHz
    "M" : 8,
    "K" : 512,
    "N" : 8,
    "SRAM_Capacity": 4,
    "SRAM_Bandwidth": 32768, # 32 TB/s
    "DataWidth": 2 
}

def select_powers_of_two_with_last(max_batch):
    powers = [2**i for i in range(max_batch.bit_length()) if 2**i < max_batch]
    if max_batch not in powers:
        powers.append(max_batch)
    return powers

def hbm_capacity_requirement(
    roofline_model,
    model_config,
    seq_context_length,
    batch_size: int
):
    hbm_storage_per_layer = 0
    # QKV Projection Weights & Biases
    hbm_storage_per_layer += model_config.get("hidden_size", 0) * model_config.get("hidden_size", 0) * 3 * roofline_model.data_width
    hbm_storage_per_layer += model_config.get("hidden_size", 0) * 3 * roofline_model.data_width
    # KV Cache
    hbm_storage_per_layer += seq_context_length * model_config.get("hidden_size", 0) * 2 * batch_size * roofline_model.data_width
    # Attention Output
    hbm_storage_per_layer += model_config.get("hidden_size", 0) * seq_context_length * batch_size * roofline_model.data_width
    # MLP
    hbm_storage_per_layer += model_config.get("hidden_size", 0) * model_config.get("intermediate_size", 0) * 2 * roofline_model.data_width
    hbm_storage_per_layer += model_config.get("intermediate_size", 0) * batch_size * roofline_model.data_width
    hbm_storage_per_layer += model_config.get("intermediate_size", 0) * 2 * roofline_model.data_width
    hbm_storage_per_layer += model_config.get("hidden_size", 0) * batch_size * roofline_model.data_width
    return hbm_storage_per_layer * model_config.get("num_hidden_layers", 0) / 1e9  # Convert to GB


def device_performance(device_model, seq_context_length, max_batch, model_config):
    batch_bound = 0
    for batch_size in range(1, max_batch):
        hbm_capacity = hbm_capacity_requirement(device_model, model_config, seq_context_length, batch_size)
        if hbm_capacity > device_model.hbm_capacity:
            break
        batch_bound = batch_size 

    roofline_performance = {}
    sampled_batch = select_powers_of_two_with_last(max_batch)
    max_tflops = device_model.get_peak_performance() / 1e9
    for batch in sampled_batch:
        peak_tflops = 2 * batch * device_model.K * device_model.operate_freq / 1e9
        roofline_performance[batch] = min(peak_tflops, max_tflops)
    
    actual_performance = {}
    # print("device width:", device_model.data_width)
    max_tilesize = device_model.hbm_bandwidth / (2 * device_model.operate_freq * device_model.data_width)
    # print("batch_bound:", batch_bound, "max_tilesize:", max_tilesize)
    sampled_batch = select_powers_of_two_with_last(batch_bound)
    for batch in sampled_batch:
        if batch > device_model.M:
            break
        compute_intensity = 2 * min(device_model.K, max_tilesize) * batch * device_model.operate_freq / 1e9
        actual_performance[batch] = min(compute_intensity, max_tflops)

    return roofline_performance, actual_performance, batch_bound

    # INSERT_YOUR_CODE

class MemoryRooflineModel:
    def __init__(self, peak_flops, mem_bandwidth, label):
        """
        peak_flops: in GFLOPs/s
        mem_bandwidth: in GB/s
        label: string for the memory type
        """
        self.peak_flops = peak_flops
        self.mem_bandwidth = mem_bandwidth
        self.label = label

    def attainable_performance(self, operational_intensity):
        """operational_intensity: array-like, FLOPs/Byte"""
        # mem_bandwidth in GB/s --> * 1e9 = bytes/s
        # But operational_intensity is already in FLOPs/Byte, so mem_bandwidth in GB/s x 1e9 x oper_intensity in FLOPs/Byte gives us FLOPs/s, /1e9 = GFLOPs/s
        return np.minimum(self.peak_flops, np.array(operational_intensity) * self.mem_bandwidth)  # GFLOPs/s

class DeviceModel:
    def __init__(self, operate_freq, M, K, N, data_width, hbm_bandwidth, hbm_capacity, sram_bandwidth=None, sram_capacity=None):
        self.operate_freq = operate_freq
        self.M = M
        self.K = K
        self.N = N
        self.data_width = data_width
        self.hbm_bandwidth = hbm_bandwidth
        self.hbm_capacity = hbm_capacity
        self.sram_bandwidth = sram_bandwidth
        self.sram_capacity = sram_capacity

    def get_peak_performance(self):
        # Assume FMA: 2 * M * K * freq
        return self.operate_freq * self.M * self.K * 2  # FLOPs/sec

    def get_roofline_models(self):
        peak_flops = self.get_peak_performance() / 1e9  # GFLOPs/s
        # bandwidth is in GB/s
        models = []
        if self.hbm_bandwidth:
            models.append(MemoryRooflineModel(peak_flops, self.hbm_bandwidth, "HBM"))
        if self.sram_bandwidth:
            models.append(MemoryRooflineModel(peak_flops, self.sram_bandwidth, "SRAM"))
        return models

def plot_device_rooflines(ax, device_model):
    operation_intensity = np.logspace(-1, 4, 1000)  # FLOPs/Byte, from 0.1 to 10,000 (log scale for clarity)
    colors = ["#377eb8", "#e41a1c", "#4daf4a", "#984ea3"]
    for idx, mem_roofline in enumerate(device_model.get_roofline_models()):
        performance = mem_roofline.attainable_performance(operation_intensity)
        ax.plot(operation_intensity, performance, label=f"{mem_roofline.label} Roofline", linewidth=2, linestyle='-', color=colors[idx % len(colors)])
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Operational Intensity (FLOPs/Byte)')
    ax.set_ylabel('Performance (GFLOPs/s)')
    ax.legend()
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
    ax.set_title("Device Roofline Model (SRAM & HBM)")

# Example usage (can be used in __main__ or in a notebook)
if __name__ == "__main__":
    fig, ax = plt.subplots(figsize=(8,6))
    device = DeviceModel(
        operate_freq=1e9, M=8, K=512, N=8, data_width=2,
        hbm_bandwidth=512, hbm_capacity=144,
        sram_bandwidth=32768, sram_capacity=4  # 32 TB/s for SRAM
    )
    plot_device_rooflines(ax, device)
    plt.savefig("device_roofline.png")

