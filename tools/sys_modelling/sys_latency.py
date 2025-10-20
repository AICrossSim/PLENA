import json
import math
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import math

class model_config:
    def __init__(self, model_param_path, hardware_config, batch_size = 1, seq_len = 2048, output_token = 128, device_num = 1):
        model_param = json.load(open(model_param_path))
        self.hidden_size = model_param["hidden_size"]
        self.num_attention_heads = model_param["num_attention_heads"]
        self.num_hidden_layers = model_param["num_hidden_layers"]
        self.intermediate_size = model_param["intermediate_size"]
        self.num_key_value_heads = model_param["num_key_value_heads"]
        self.vocab_size = model_param["vocab_size"]
        self.default_seq_len = seq_len
        self.head_dim = self.hidden_size // self.num_attention_heads
        self.num_head_groups = self.num_attention_heads // self.num_key_value_heads
        self.vocab_size = model_param["vocab_size"]
        self.DataTypeSize = 2
        self.theoratical_frequency = 10**9          # 1 GHz
        self.hardware_config = hardware_config
        self.output_token = output_token
        self.batch_size = batch_size
        self.kv_size = seq_len
        self.device_num = device_num


    def rms_layer(self, mode = "prefill"):
        if mode == "prefill":
            setting_inst_num = 10
            loop_inst_num = 8
            loop_num = self.hidden_size // self.hardware_config["VLEN"]
            instruction_num = 0
            instruction_num += setting_inst_num
            instruction_num += loop_num * loop_inst_num * self.default_seq_len
        elif mode == "decode":
            setting_inst_num = 10
            loop_inst_num = 8
            loop_num = self.hidden_size // self.hardware_config["VLEN"]
            instruction_num = 0
            instruction_num += setting_inst_num
            instruction_num += loop_num * loop_inst_num            
        return instruction_num * self.batch_size

    def projection(self, mode = "prefill"):
        if mode == "prefill":
            overall_inst_num = 0
            # Q, K Projection + RoPE
            overall_inst_num += self.batch_size * (math.ceil(self.hidden_size / self.hardware_config["BLEN"]) * (math.ceil(self.hidden_size / self.hardware_config["MLEN"]) * (math.ceil(self.default_seq_len / self.hardware_config["BLEN"]) * 2 + 10)))
            overall_inst_num += self.batch_size * (self.num_attention_heads * (self.default_seq_len // self.hardware_config["VLEN"])) * 3

            overall_inst_num += self.batch_size * (math.ceil((self.num_key_value_heads * self.head_dim) / self.hardware_config["BLEN"]) * (math.ceil(self.hidden_size / self.hardware_config["MLEN"]) * (math.ceil(self.default_seq_len / self.hardware_config["BLEN"]) * 2 + 10)))
            overall_inst_num += self.batch_size * (self.num_key_value_heads * (self.default_seq_len // self.hardware_config["VLEN"])) * 3

            # V
            overall_inst_num += self.batch_size * (math.ceil((self.num_key_value_heads * self.head_dim) / self.hardware_config["BLEN"]) * (math.ceil(self.hidden_size / self.hardware_config["MLEN"]) * (math.ceil(self.default_seq_len / self.hardware_config["BLEN"]) * 2 + 10)))
        
        elif mode == "decode":
            overall_inst_num = 0
            # Q, K Projection + RoPE
            overall_inst_num +=  (math.ceil(self.hidden_size / self.hardware_config["BLEN"]) * (math.ceil(self.hidden_size / self.hardware_config["MLEN"]) * 2 + 10))
            overall_inst_num += self.batch_size * (self.num_attention_heads) * 4

            overall_inst_num +=  (math.ceil((self.num_key_value_heads * self.head_dim) / self.hardware_config["BLEN"]) * (math.ceil(self.hidden_size / self.hardware_config["MLEN"]) * 2 + 10))
            overall_inst_num += self.batch_size * (self.num_key_value_heads) * 4

            # V
            overall_inst_num += (math.ceil((self.num_key_value_heads * self.head_dim) / self.hardware_config["BLEN"]) * (math.ceil(self.hidden_size / self.hardware_config["MLEN"]) * 2 + 10))
        
        return overall_inst_num
    
    def flash_attention(self, mode = "prefill"):
        overall_inst_num = 0
        mlen = self.hardware_config["MLEN"]
        blen = self.hardware_config["BLEN"]
        tile_in_atten = min(self.head_dim, mlen)
        if mode == "prefill":
        # Outer loop
            for i in range(self.default_seq_len // self.hardware_config["MLEN"]):
                for j in range((self.default_seq_len // self.hardware_config["MLEN"]) * self.num_key_value_heads):
                    overall_inst_num += 4 + (mlen // blen) * 8 + 3 # MLEN * MLEN
                    overall_inst_num += 2 + mlen * 5  # Softmax
                    overall_inst_num += math.ceil(self.head_dim / mlen) * (9 + 4 + (math.ceil(tile_in_atten / blen)) * 8 + 3) #PV
                    overall_inst_num += math.ceil(self.head_dim / mlen) * (1+ tile_in_atten * 3) #Compute O
                    overall_inst_num += 8
                    # overall_inst_num += 2 + mlen * 4
        elif mode == "decode":
            for j in range(math.ceil(self.kv_size / self.hardware_config["MLEN"]) ):
                overall_inst_num += (4 + (tile_in_atten // blen) * 4 + 3) * self.num_key_value_heads
                overall_inst_num += 2 + mlen * 5  # Softmax
                overall_inst_num += math.ceil(self.head_dim / mlen) * (9 + 4 + math.ceil((tile_in_atten / blen)) * 8 + 3) #PV
                overall_inst_num += math.ceil(self.head_dim / mlen) * (1+ tile_in_atten * 3) #Compute O
                overall_inst_num += 8
                # overall_inst_num += 2 + mlen * 2
            self.kv_size = self.kv_size + 1
        return overall_inst_num * self.batch_size


    def residual (self, mode = "prefill"):
        overall_inst_num = 0
        # -- Residual
        if mode == "prefill":
            iteration = self.hidden_size // self.hardware_config["VLEN"]
            overall_inst_num = (5 * iteration + 3) * self.default_seq_len
        elif mode == "decode":
            iteration = self.hidden_size // self.hardware_config["VLEN"]
            overall_inst_num = 5 * iteration + 3
        return overall_inst_num

    def feed_forward(self, mode = "prefill"):
        mlen = self.hardware_config["MLEN"]
        vlen = self.hardware_config["VLEN"]
        blen = self.hardware_config["BLEN"]

        overall_inst_num = 0
        # -- MLP
        if mode == "prefill":
            overall_inst_num += 2 * math.ceil(self.intermediate_size / blen) * math.ceil(self.hidden_size / mlen) * 4 * (self.default_seq_len // blen)
            overall_inst_num += math.ceil(self.intermediate_size / vlen) * 5
            overall_inst_num += math.ceil(self.intermediate_size / blen) * math.ceil(self.hidden_size / mlen) * 4 * (self.default_seq_len // blen)
            overall_inst_num = (overall_inst_num) 
        elif mode == "decode":
            overall_inst_num += 2 * math.ceil(self.intermediate_size / blen) * math.ceil(self.hidden_size / mlen) * 4
            overall_inst_num += math.ceil(self.intermediate_size / vlen) * 5
            overall_inst_num += math.ceil(self.intermediate_size / blen) * math.ceil(self.hidden_size / mlen) * 4
        return overall_inst_num

    def embeddings(self, mode = "prefill"):
        mlen = self.hardware_config["MLEN"]
        vlen = self.hardware_config["VLEN"]
        blen = self.hardware_config["BLEN"]
        overall_inst_num = 3
        if mode == "prefill":
            overall_inst_num += self.default_seq_len * math.ceil(self.hidden_size / blen) * math.ceil(self.hidden_size / mlen) * (blen * 2 + 1) + 4
        elif mode == "decode":
            overall_inst_num += math.ceil(self.hidden_size / blen) * math.ceil(self.hidden_size / mlen) * (blen * 2 + 1) + 4
        return overall_inst_num
    
    def lm_head(self):
        mlen = self.hardware_config["MLEN"]
        vlen = self.hardware_config["VLEN"]
        blen = self.hardware_config["BLEN"]
        overall_inst_num = 3
        overall_inst_num += (math.ceil(self.hidden_size / blen) * math.ceil(self.vocab_size / mlen) * (blen * 2 + 1) + 4)
        return overall_inst_num

    def compute_prefill_time(self):
        mode = "prefill"
        overall_inst_num = 0
        overall_inst_num += self.embeddings(mode)
        for i in range(self.num_hidden_layers):
            overall_inst_num += self.rms_layer(mode)
            overall_inst_num += self.projection(mode)
            overall_inst_num += self.flash_attention(mode)
            overall_inst_num += self.residual(mode)
            overall_inst_num += self.rms_layer(mode)
            overall_inst_num += self.feed_forward(mode)
            # overall_inst_num += self.residual(mode)
        # overall_inst_num += self.rms_layer()
        overall_inst_num += self.lm_head()
        # print("Overall instruction number: ", overall_inst_num)
        overall_exe_cycle = overall_inst_num * 2
        theoratical_execution_time = overall_exe_cycle / self.theoratical_frequency
        # print("Theoratical execution time: ", theoratical_execution_time)
        return theoratical_execution_time

    def compute_decode_time(self, output_token_size):
        mode = "decode"
        overall_inst_num = 0
        for j in range (output_token_size):
            for i in range (self.num_hidden_layers):
                overall_inst_num += self.rms_layer(mode)
                overall_inst_num += self.projection(mode)
                overall_inst_num += self.flash_attention(mode)
                overall_inst_num += self.residual(mode)
                overall_inst_num += self.rms_layer(mode)
                overall_inst_num += self.feed_forward(mode)
        # print("Overall instruction number: ", overall_inst_num)
        overall_exe_cycle = overall_inst_num * 2 # avg 3 execution cycles
        theoratical_execution_time = overall_exe_cycle / self.theoratical_frequency
        # print("Theoratical execution time: ", theoratical_execution_time)
        return theoratical_execution_time


    def compute_overall_perf(self):
        ttft = (self.compute_prefill_time() + self.compute_decode_time(1)) / self.device_num
        tps = (self.device_num * (self.batch_size * self.output_token)) / self.compute_decode_time(self.output_token // self.device_num)
        return ttft, tps




if __name__ == "__main__":
    model = model_config("Model_Lib/llama-3.1-8b.json", batch_size=4)
    MLEN = 64
    seq_len = 2048
    overall_inst_num, theoratical_execution_time = model.compute_overall_inst()
    print("Overall Instruction Number: ", overall_inst_num)





        

