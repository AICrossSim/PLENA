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
        self.input_token = seq_len
        self.output_token = output_token
        self.head_dim = self.hidden_size // self.num_attention_heads
        self.num_head_groups = self.num_attention_heads // self.num_key_value_heads
        self.vocab_size = model_param["vocab_size"]
        self.DataTypeSize = 2
        self.theoratical_frequency = 10**9          # 1 GHz
        self.hardware_config = hardware_config
        self.batch_size = batch_size
        self.kv_size = seq_len
        self.device_num = device_num
        print("=" * 15, "Model Settings","=" * 15)
        print("hardware config: \n", self.hardware_config)
        print("batch size: ", self.batch_size)
        print("input token: ", self.input_token)
        print("output token: ", self.output_token)
        print("head dim: ", self.head_dim)
        print("num key value heads: ", self.num_key_value_heads)
        print("num attention heads: ", self.num_attention_heads)
        print("num hidden layers: ", self.num_hidden_layers)
        print("intermediate size: ", self.intermediate_size)
        print("vocab size: ", self.vocab_size)
        print("=" * 25)

    def rms_layer(self, mode = "prefill"):
        if mode == "prefill":
            setting_inst_num = 10
            loop_inst_num = 8
            loop_num = self.hidden_size // self.hardware_config["VLEN"]
            instruction_num = 0
            instruction_num += setting_inst_num
            instruction_num += loop_num * loop_inst_num * self.input_token
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
            overall_inst_num += self.batch_size * (math.ceil(self.hidden_size / self.hardware_config["BLEN"]) * (math.ceil(self.hidden_size / self.hardware_config["MLEN"]) * (math.ceil(self.input_token / self.hardware_config["BLEN"]) * 2 + 10)))
            overall_inst_num += self.batch_size * (self.num_attention_heads * (self.input_token // self.hardware_config["VLEN"])) * 3

            overall_inst_num += self.batch_size * (math.ceil((self.num_key_value_heads * self.head_dim) / self.hardware_config["BLEN"]) * (math.ceil(self.hidden_size / self.hardware_config["MLEN"]) * (math.ceil(self.input_token / self.hardware_config["BLEN"]) * 2 + 10)))
            overall_inst_num += self.batch_size * (self.num_key_value_heads * (self.input_token // self.hardware_config["VLEN"])) * 3

            # V
            overall_inst_num += self.batch_size * (math.ceil((self.num_key_value_heads * self.head_dim) / self.hardware_config["BLEN"]) * (math.ceil(self.hidden_size / self.hardware_config["MLEN"]) * (math.ceil(self.input_token / self.hardware_config["BLEN"]) * 2 + 10)))
        
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
            for kv_head_index in range(self.num_key_value_heads):
                for i in range(math.ceil(self.input_token // self.hardware_config["MLEN"])):
                    overall_inst_num += mlen * 2 # Reset                    
                    for j in range(math.ceil(self.input_token // self.hardware_config["MLEN"])):
                        overall_inst_num += mlen * 2 # QKT
                        overall_inst_num += 2 + mlen * 14  # Softmax
                        overall_inst_num += math.ceil(self.head_dim / blen) * (4 + math.ceil(mlen / blen) * 4) #PV
                        overall_inst_num += mlen * 5 + 4 #Compute O
                        overall_inst_num += 8
            self.kv_size = self.input_token 
        elif mode == "decode":
            for kv_head_index in range(self.num_key_value_heads):
                for i in range(math.ceil(self.kv_size // self.hardware_config["MLEN"])):
                    # overall_inst_num += mlen * 2 # Reset                    
                    overall_inst_num += mlen * 2 # QKT
                    overall_inst_num += 2 + mlen * 14 # Softmax
                    overall_inst_num += math.ceil(self.head_dim / blen) * (4 + math.ceil(mlen / blen) * 4) #PV
                    overall_inst_num += mlen * 5 + 4 #Compute O
                    overall_inst_num += 8
            self.kv_size = self.kv_size + 1
        return overall_inst_num * self.batch_size


    def residual (self, mode = "prefill"):
        overall_inst_num = 0
        # -- Residual
        if mode == "prefill":
            iteration = self.hidden_size // self.hardware_config["VLEN"]
            overall_inst_num = (5 * iteration + 3) * self.input_token
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
            overall_inst_num += 2 * math.ceil(self.intermediate_size / blen) * math.ceil(self.hidden_size / mlen) * 4 * (self.input_token // blen)
            overall_inst_num += math.ceil(self.intermediate_size / vlen) * 5
            overall_inst_num += math.ceil(self.intermediate_size / blen) * math.ceil(self.hidden_size / mlen) * 4 * (self.input_token // blen)
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
            overall_inst_num += self.input_token * math.ceil(self.hidden_size / blen) * math.ceil(self.hidden_size / mlen) * (blen * 2 + 1) + 4
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
        overall_exe_cycle = overall_inst_num * 2
        theoratical_execution_time = overall_exe_cycle / self.theoratical_frequency
        print("\n")
        print("=" * 5,"Prefill Theoratical execution distribution: ","=" * 5)
        print(f"RMS Layer: {self.rms_layer(mode) * self.num_hidden_layers / overall_inst_num * 100}%")
        print(f"Projection: {self.projection(mode) * self.num_hidden_layers / overall_inst_num * 100}%")
        print(f"Flash Attention: {self.flash_attention(mode) * self.num_hidden_layers / overall_inst_num * 100}%")
        print(f"Residual: {self.residual(mode) * self.num_hidden_layers / overall_inst_num * 100}%")
        print(f"Feed Forward: {self.feed_forward(mode) * self.num_hidden_layers / overall_inst_num * 100}%")
        print(f"LM Head: {self.lm_head() / overall_inst_num * 100}%")
        return theoratical_execution_time

    def compute_decode_time(self, output_token_size):
        mode = "decode"
        overall_inst_num = 0
        rms_count = 0
        projection_count = 0
        flash_attention_count = 0
        residual_count = 0
        feed_forward_count = 0
        for j in range (output_token_size):
            for i in range (self.num_hidden_layers):
                rms_count += self.rms_layer(mode)
                projection_count += self.projection(mode)
                flash_attention_count += self.flash_attention(mode)
                residual_count += self.residual(mode)
                rms_count += self.rms_layer(mode)
                feed_forward_count += self.feed_forward(mode)
        overall_inst_num = rms_count + projection_count + flash_attention_count + residual_count + feed_forward_count
        overall_exe_cycle = overall_inst_num * 2 # avg 2 execution cycles
        theoratical_execution_time = overall_exe_cycle / self.theoratical_frequency
        print("\n")
        print("=" * 5,"Decode Theoratical execution distribution: ","=" * 5)
        print(f"RMS Layer: {rms_count / overall_inst_num * 100}%")
        print(f"Projection: {projection_count / overall_inst_num * 100}%")
        print(f"Flash Attention: {flash_attention_count / overall_inst_num * 100}%")
        print(f"Residual: {residual_count / overall_inst_num * 100}%")
        print(f"Feed Forward: {feed_forward_count / overall_inst_num * 100}%")
        return theoratical_execution_time


    def compute_overall_perf(self):
        ttft = (self.compute_prefill_time() + self.compute_decode_time(1)) / self.device_num
        tps = (self.device_num * (self.batch_size * self.output_token)) / self.compute_decode_time(self.output_token // self.device_num)
        return ttft, tps






        

