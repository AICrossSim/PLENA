import json
import math
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


import math

def find_max_x(const1, const2):
    """
    Finds the maximum power-of-2 integer x satisfying the inequality:
    x^2 * const1 + x * const1 <= const2
    
    :param const1: A given constant (real number)
    :param const2: A given constant (real number)
    :return: The maximum power-of-2 integer x satisfying the inequality
    """
    if const1 <= 0:
        return None  # Avoid invalid cases where const1 is non-positive
    
    # Solve the quadratic equation x^2 * const1 + x * const1 - const2 = 0
    a, b, c = const1, const1, -const2
    
    # Compute the discriminant
    discriminant = b**2 - 4*a*c
    
    if discriminant < 0:
        return None  # No real solutions exist
    
    # Compute the two roots
    sqrt_discriminant = math.sqrt(discriminant)
    x1 = (-b + sqrt_discriminant) / (2 * a)
    x2 = (-b - sqrt_discriminant) / (2 * a)
    
    # The maximum integer satisfying the inequality is the floor of the positive root
    max_x = math.floor(max(x1, x2))
    
    # Find the maximum power of 2 less than or equal to max_x
    power_of_2_x = 2 ** int(math.log2(max_x)) if max_x > 0 else None
    
    return power_of_2_x


class model_config:
    def __init__(self, model_param_path, hardware_config, batch_size = 1, seq_len = 2048, hbm_bandwidth = 256):
        model_param = json.load(open(model_param_path))
        self.hidden_size = model_param["hidden_size"]
        self.num_attention_heads = model_param["num_attention_heads"]
        self.num_hidden_layers = model_param["num_hidden_layers"]
        self.intermediate_size = model_param["intermediate_size"]
        self.num_key_value_heads = model_param["num_key_value_heads"]
        self.attention_bias = model_param["attention_bias"]
        self.vocab_size = model_param["vocab_size"]
        self.default_seq_len = seq_len
        self.head_dim = self.hidden_size // self.num_attention_heads
        self.num_head_groups = self.num_attention_heads // self.num_key_value_heads
        self.vocab_size = model_param["vocab_size"]
        self.DataTypeSize = 4
        self.hbm_bandwidth = hbm_bandwidth        # GigaByte per second
        self.theoratical_frequency = 10**9          # 1 GHz
        self.hardware_config = hardware_config
        self.batch_size = batch_size


    def rms_layer(self):
        setting_inst_num = 10
        loop_inst_num = 8
        loop_num = self.hidden_size // self.hardware_config["VLEN"]
        instruction_num = 0
        instruction_num += setting_inst_num
        instruction_num += loop_num * loop_inst_num
        return instruction_num * self.batch_size

    def projection(self):
        overall_inst_num = 0
        # Q, K Projection + RoPE
        overall_inst_num += self.batch_size * (self.hidden_size // self.hardware_config["BLEN"]) * (self.hidden_size // self.hardware_config["MLEN"]) * (self.default_seq_len // self.hardware_config["BLEN"]) * 3 + 10
        overall_inst_num += self.batch_size * (self.num_attention_heads * self.default_seq_len) * 10

        overall_inst_num += self.batch_size * ((self.num_key_value_heads * self.head_dim) // self.hardware_config["BLEN"]) * (self.hidden_size // self.hardware_config["MLEN"]) * (self.default_seq_len // self.hardware_config["BLEN"]) * 3 + 10
        overall_inst_num += self.batch_size * (self.num_key_value_heads * self.default_seq_len) * 10

        # V
        overall_inst_num += self.batch_size * ((self.num_key_value_heads * self.head_dim) // self.hardware_config["BLEN"]) * (self.hidden_size // self.hardware_config["MLEN"]) * (self.default_seq_len // self.hardware_config["BLEN"]) * 3 + 10
        return overall_inst_num
    
    def flash_attention(self):
        overall_inst_num = 0
        mlen = self.hardware_config["MLEN"]
        blen = self.hardware_config["BLEN"]
        # Outer loop
        for i in range(self.default_seq_len // self.hardware_config["MLEN"]):
            for j in range(self.default_seq_len // self.hardware_config["MLEN"]):
                overall_inst_num += 4 + (mlen // blen) ** 2 * 8 + 3 # MLEN * MLEN
                overall_inst_num += 2 + mlen * 30  # Softmax
                overall_inst_num += max(1, self.head_dim // mlen) * (9 + 4 + (mlen // blen) ** 2 * 8 + 3) #PV
                overall_inst_num += max(1, self.head_dim // mlen) * (1+ mlen * 5) #Compute O
                overall_inst_num += 8
                overall_inst_num += 2 + mlen * 4
        return overall_inst_num * self.batch_size
    


    def residual (self):
        overall_inst_num = 0
        # -- Residual
        iteration = self.hidden_size // self.hardware_config["VLEN"]
        overall_inst_num = 5 * iteration + 3
        return overall_inst_num

    def feed_forward(self):
        mlen = self.hardware_config["MLEN"]
        vlen = self.hardware_config["VLEN"]
        blen = self.hardware_config["BLEN"]

        overall_inst_num = 0
        # -- MLP
        overall_inst_num += 2 * (self.intermediate_size // blen) * (self.hidden_size // mlen) * 4
        overall_inst_num += (self.intermediate_size // vlen) * 5
        overall_inst_num += (self.intermediate_size // blen) * (self.hidden_size // mlen) * 4
        return overall_inst_num

    def embeddings(self):
        mlen = self.hardware_config["MLEN"]
        vlen = self.hardware_config["VLEN"]
        blen = self.hardware_config["BLEN"]
        overall_inst_num = 3
        overall_inst_num += (self.hidden_size // blen) * (self.hidden_size // mlen) * (blen * 2 + 1) + 4
        
    def lm_head(self):
        mlen = self.hardware_config["MLEN"]
        vlen = self.hardware_config["VLEN"]
        blen = self.hardware_config["BLEN"]
        overall_inst_num = 3
        overall_inst_num += (self.hidden_size // blen) * (self.vocab_size // mlen) * (blen * 2 + 1) + 4
        
        return overall_inst_num


    def compute_overall_inst(self):
        overall_inst_num = 0
        for i in range(self.num_hidden_layers):
            overall_inst_num += self.rms_layer()
            overall_inst_num += self.projection()
            overall_inst_num += self.flash_attention()
            overall_inst_num += self.residual()
            overall_inst_num += self.rms_layer()
            overall_inst_num += self.feed_forward()
            overall_inst_num += self.residual()
        # overall_inst_num += self.rms_layer()
        overall_inst_num += self.lm_head()
        # print("Overall instruction number: ", overall_inst_num)
        overall_exe_cycle = overall_inst_num * 2 # avg 3 execution cycles
        theoratical_execution_time = overall_exe_cycle / self.theoratical_frequency
        # print("Theoratical execution time: ", theoratical_execution_time)
        return overall_inst_num, theoratical_execution_time
    
    def resource_utilization_estimation(self, TileSize):
        MVM_SRAM = 2 * TileSize * TileSize * self.DataTypeSize  
        print("MVM SRAM Utilization: ", MVM_SRAM  / 1024 / 8, "KB")
        Scratchpad_SRAM = 4 * TileSize * self.DataTypeSize
        print("Scratchpad SRAM Utilization: ", Scratchpad_SRAM / 1024 / 8, "KB")
        SRAM_Utilization = MVM_SRAM + Scratchpad_SRAM
        print("SRAM Utilization: ", SRAM_Utilization / 1024 / 8, "KB")
        return SRAM_Utilization
    

    def matrix_mult_flop_in_overall_process(self, TileSize):
        max_flops_per_cycle = TileSize * TileSize * 2 * self.batch_size
        inst_num = 0
        # Q, K, V Projection
        inst_num += 3 * (self.hidden_size // TileSize) ** 2
        # Flash Attention
        inst_num += (self.head_dim // TileSize) * (self.seq_len // TileSize) * 2
        # MLP
        inst_num += (self.hidden_size * self.intermediate_size) // (TileSize * TileSize)

        return (inst_num * max_flops_per_cycle * self.num_hidden_layers)

    def vector_operation_flop_in_overall_process(self, TileSize):
        max_flops_per_cycle = TileSize * 2 * self.batch_size
        inst_num = 0
        # RMS
        inst_num += 2 * (self.hidden_size // TileSize)
        # Q, K, V Projection
        inst_num += 3 * (self.hidden_size // TileSize)
        # Flash Attention
        inst_num += (self.head_dim // TileSize) * (self.seq_len // TileSize)
        # Residual
        inst_num += 2 * (self.hidden_size // TileSize)
        # Feed Forward
        inst_num += 2 * (self.hidden_size // TileSize)
        # MLP
        inst_num += 2 * (self.hidden_size // TileSize)
        return (inst_num * max_flops_per_cycle * self.num_hidden_layers)
    
    def compute_theoratical_performance(self, TileSize):
        matrix_mult_flop = self.matrix_mult_flop_in_overall_process(TileSize)
        vector_operation_flop = self.vector_operation_flop_in_overall_process(TileSize)
        total_flop = matrix_mult_flop + vector_operation_flop
        mcycles = self.compute_overall_inst(TileSize)[0] * 8
        print("Total FLOP: ", total_flop, "Total Instruction: ", mcycles)
        flops = ((total_flop // mcycles) * self.theoratical_frequency) / 10**9
        print("Theoratical Performance: ", flops, "GFLOP/s")
        return flops
    

    def determine_max_TileSize(self, batch_size, hbm_bandwidth):
        cycle_bandwidth = (hbm_bandwidth * 1024 * 1024 * 1024 * 8) / (self.DataTypeSize * self.theoratical_frequency)
        max_TileSize = find_max_x(batch_size, cycle_bandwidth)
        print("batch size: ", batch_size, "HBM Bandwidth: ", hbm_bandwidth, "Max Tile Size: ", max_TileSize)
        return max_TileSize




if __name__ == "__main__":
    model = model_config("Model_Lib/llama-3.1-8b.json")
    # # plot a graph, 
    # batch_size_selection = [1, 2, 4, 8]
    # hbm_bandwidth_selection = [64, 128, 256]
    # flops = np.zeros((len(batch_size_selection), len(hbm_bandwidth_selection)))
    # for j in range(len(hbm_bandwidth_selection)):
    #     for i in range(len(batch_size_selection)):      
    #         max_TileSize = model.determine_max_TileSize(batch_size_selection[i], hbm_bandwidth_selection[j])
    #         flops[i][j] = model.compute_theoratical_performance(max_TileSize)


    # fig = plt.figure()
    # ax = fig.add_subplot(111, projection='3d')
    # X, Y = np.meshgrid(hbm_bandwidth_selection, batch_size_selection)
    # ax.plot_surface(X, Y, flops, cmap='viridis')
    # ax.set_xlabel('HBM Bandwidth (GB/s)')
    # ax.set_ylabel('Batch Size')
    # ax.set_zlabel('Theoratical Performance (GFLOP/s)')
    # plt.show()
    MLEN = 64
    overall_inst_num, theoratical_execution_time = model.compute_overall_inst(MLEN)
    print("Overall Instruction Number: ", overall_inst_num)





        

