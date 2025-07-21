import matplotlib.pyplot as plt
import numpy as np
from utils import load_json
from pathlib import Path
import os

# HBM Settings
Operate_Freq = 1e9  # 1 GHz
Batch_Size = 16
MLEN = 128
BLEN = 16
DataWidth = 1 # 1 byte per element
HBM_Bandwidth = 460e9  # 460 GB/s
HBM_Capacity = 100e9  # 100 GB




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

    def plot_roofline(self):
        operation_intensity = np.linspace(0, 1000, 1000)
        performance = self.get_attainable_performance(operation_intensity)
        plt.figure(figsize=(10, 6))
        plt.plot(operation_intensity, performance, label='Attainable Performance')
        plt.axhline(self.get_peak_performance()  / 1e9 , color='r', linestyle='--', label='Peak Performance')
        plt.xscale('log')
        plt.yscale('log')
        plt.xlabel('Operation Intensity (FLOPs/Byte)')
        plt.ylabel('Attainable Performance (GFLOPs/s)')
        plt.title('Roofline Model')
        plt.legend()
        plt.savefig('roofline_model.png')

def square_comman_systolic_array(
    roofline_model
):
    pass


def FC_attainable_performance(
    roofline_model,
    model_config
):
    pass



if __name__ == "__main__":
    config_parent_path = Path(__file__).resolve().parents[3]
    model_config_path = os.path.join(config_parent_path, "doc/Model_Lib/llama-3.1-8b.json")
    roofline_model = RooflineMoel()
    roofline_model.plot_roofline()
    print("Roofline model plot saved as 'roofline_model.png'.")