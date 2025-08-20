import os
from typing import Dict, List, Any, Optional
import json

class attn_model_config:
    def __init__(self, model_param_path, hardware_config, batch_size = 1, seq_len = 2048, output_token = 128, device_num = 1):
        model_param = json.load(open(model_param_path))
        self.hidden_size = model_param["hidden_size"]
        self.num_attention_heads = model_param["num_attention_heads"]
        self.num_hidden_layers = model_param["num_hidden_layers"]
        self.intermediate_size = model_param["intermediate_size"]
        self.num_key_value_heads = model_param["num_key_value_heads"]
        self.vocab_size = model_param["vocab_size"]
        self.input_seq_len = seq_len
        self.head_dim = self.hidden_size // self.num_attention_heads
        self.num_head_groups = self.num_attention_heads // self.num_key_value_heads
        self.vocab_size = model_param["vocab_size"]
        self.DataTypeSize = 2
        self.theoratical_frequency = 10**9          # 1 GHz
        self.hardware_config = hardware_config
        self.output_token = output_token
        self.batch_size = batch_size
        print(f"Batch size: {self.batch_size}")
        self.kv_size = seq_len
        self.device_num = device_num
        self.M = hardware_config["BLEN"]
        self.K = hardware_config["MLEN"]
        self.N = self.M

    def _report_flash_attn_utilization(self, mode = "prefill") -> None:
        """
        Report the utilization of flash attention for a given node.
        """
        batch_size = self.batch_size
        hidden_size = self.hidden_size
        num_attn_heads = self.num_attention_heads
        num_kv_heads = self.num_key_value_heads

        head_dim = self.head_dim
        input_token_size = self.input_seq_len
        theoretical_operation = 0
        attainable_operation = 0
        overall_operation_amount = 0
        
        # Decoding
        if mode == "prefill":
            # Projection
            operation_amount = ((head_dim * num_attn_heads)  // self.M) * ( hidden_size // self.K) * (self.input_seq_len // self.M) + ((head_dim * num_kv_heads) // self.M) * ( hidden_size// self.K) * (self.input_seq_len // self.M) * 2
            overall_operation_amount    += operation_amount
            attainable_operation        += operation_amount * (self.M * self.K * self.N)
            theoretical_operation       += operation_amount * (self.M * self.K * self.N)
            # QKT
            operation_amount =  batch_size * num_attn_heads * (head_dim // self.K) * (self.input_seq_len  // self.N)
            overall_operation_amount    += operation_amount
            attainable_operation        += operation_amount * (self.M * min(self.K, head_dim))
            theoretical_operation       += operation_amount * (self.M * self.K * self.N)

            # PV
            operation_amount =  batch_size * num_attn_heads * (input_token_size // self.K) * (head_dim // self.N)
            overall_operation_amount    += operation_amount
            attainable_operation        += operation_amount * (self.M * min(self.K, head_dim))
            theoretical_operation       += operation_amount * (self.M * self.K * self.N)
        elif mode == "decode":
            # Projection
            operation_amount = ((head_dim * num_attn_heads)  // self.M) * ( hidden_size // self.K) + ((head_dim * num_kv_heads) // self.M) * ( hidden_size// self.K) * 2
            overall_operation_amount    += operation_amount
            attainable_operation        += operation_amount * (self.M * self.K * min(self.batch_size, self.N))
            theoretical_operation       += operation_amount * (self.M * self.K * self.N)

            # QKT
            operation_amount =  batch_size * num_attn_heads * (head_dim // self.K) * (self.kv_size // self.N)
            overall_operation_amount    += operation_amount
            attainable_operation        += operation_amount * (self.M * min(self.K, head_dim))
            theoretical_operation       += operation_amount * (self.M * self.K * self.N)

            # PV
            operation_amount =  batch_size * num_attn_heads * (self.kv_size // self.K) * (head_dim // self.N)
            overall_operation_amount    += operation_amount
            attainable_operation        += operation_amount * (self.M * min(self.K, head_dim))
            theoretical_operation       += operation_amount * (self.M * self.K * self.N)
            self.kv_size = self.kv_size + 1

        return [operation_amount, attainable_operation, theoretical_operation]

    def _report_embedding_utilization(self, mode = "prefill") -> None:
        """
        Report the utilization of flash attention for a given node.
        """

        batch_size = self.batch_size
        hidden_size = self.hidden_size

        theoretical_operation = 0
        attainable_operation = 0

        if mode == "prefill":
            # Assuming Decoding only
            operation_amount = (hidden_size // self.M) * (hidden_size // self.K) * (self.input_seq_len // self.N)
            attainable_operation += operation_amount * (self.M * self.K * self.N)
            theoretical_operation += operation_amount * (self.M * self.K * self.N)
        elif mode == "decode":
            operation_amount = (hidden_size // self.M) * (hidden_size // self.K)
            attainable_operation += operation_amount * (self.M * self.K * min(self.batch_size, self.N))
            theoretical_operation += operation_amount * (self.M * self.K * self.N)

        return [operation_amount, attainable_operation, theoretical_operation]

    def _report_ffn_utilization(self, mode = "prefill") -> None:
        """
        Report the utilization of flash attention for a given node.
        """

        batch_size = self.batch_size
        hidden_size = self.hidden_size
        intermediate_size = self.intermediate_size
        overall_operation_amount = 0
        theoretical_operation = 0
        attainable_operation = 0

        if mode == "prefill":
            # Up Projection
            operation_amount = (intermediate_size // self.M) * (hidden_size // self.K) * (self.input_seq_len // self.N)
            overall_operation_amount += operation_amount
            attainable_operation += operation_amount * (self.M * self.K * self.N)
            theoretical_operation += operation_amount * (self.M * self.K * self.N)

            # Gate Projection
            operation_amount = (intermediate_size // self.M) * (hidden_size // self.K) * (self.input_seq_len // self.N)
            overall_operation_amount += operation_amount
            attainable_operation += operation_amount * (self.M * self.K * self.N)
            theoretical_operation += operation_amount * (self.M * self.K * self.N)

            # Down Projection
            operation_amount = (hidden_size // self.M) * (intermediate_size // self.K) * (self.input_seq_len // self.N)
            overall_operation_amount += operation_amount
            attainable_operation += operation_amount * (self.M * self.K * self.N)
            theoretical_operation += operation_amount * (self.M * self.K * self.N)

        elif mode == "decode":
            operation_amount = (intermediate_size // self.M) * (hidden_size // self.K)
            overall_operation_amount += operation_amount
            attainable_operation += operation_amount * (self.M * self.K * min(self.batch_size, self.N))
            theoretical_operation += operation_amount * (self.M * self.K * self.N)

            # Gate Projection
            operation_amount = (intermediate_size // self.M) * (hidden_size // self.K)
            overall_operation_amount += operation_amount
            attainable_operation += operation_amount * (self.M * self.K * min(self.batch_size, self.N))
            theoretical_operation += operation_amount * (self.M * self.K * self.N)

            # Down Projection
            operation_amount = (hidden_size // self.M) * (intermediate_size // self.K) 
            overall_operation_amount += operation_amount
            attainable_operation += operation_amount * (self.M * self.K * min(self.batch_size, self.N))
            theoretical_operation += operation_amount * (self.M * self.K * self.N)


        return [overall_operation_amount, attainable_operation, theoretical_operation]



    def _report_prefill_utilization(self):
        
        overall_operations = {"embedding": 0, "attention": 0, "ffn": 0, "lm_head": 0}
        overall_attainable_FLOPS = {"embedding": 0, "attention": 0, "ffn": 0, "lm_head": 0}
        overall_theoretical_FLOPS = {"embedding": 0, "attention": 0, "ffn": 0, "lm_head": 0}
        single_op_operation = self._report_embedding_utilization("prefill")
        overall_operations["embedding"] += (single_op_operation[0] * 2) / (10 ** 9)
        overall_attainable_FLOPS["embedding"] += (single_op_operation[1] * 2) / (10 ** 9)
        overall_theoretical_FLOPS["embedding"] += (single_op_operation[2] * 2) / (10 ** 9)
        for i in range(self.num_hidden_layers):
            single_op_operation = self._report_flash_attn_utilization("prefill")
            overall_operations["attention"] += single_op_operation[0] / (10 ** 9)
            overall_attainable_FLOPS["attention"] += single_op_operation[1] / (10 ** 9)
            overall_theoretical_FLOPS["attention"] += single_op_operation[2] / (10 ** 9)

            single_op_operation = self._report_ffn_utilization("prefill")
            overall_operations["ffn"] += single_op_operation[0] / (10 ** 9)
            overall_attainable_FLOPS["ffn"] += single_op_operation[1] / (10 ** 9)
            overall_theoretical_FLOPS["ffn"] += single_op_operation[2] / (10 ** 9)

        return {
            "operations": overall_operations,
            "attainable_FLOPS": overall_attainable_FLOPS,
            "theoretical_FLOPS": overall_theoretical_FLOPS
        }
    
    def _report_decode_utilization(self):
        overall_operations = {"embedding": 0, "attention": 0, "ffn": 0, "lm_head": 0}
        overall_attainable_FLOPS = {"embedding": 0, "attention": 0, "ffn": 0, "lm_head": 0}
        overall_theoretical_FLOPS = {"embedding": 0, "attention": 0, "ffn": 0, "lm_head": 0}
        for j in range (self.output_token):
            per_token_operations = {"embedding": 0, "attention": 0, "ffn": 0, "lm_head": 0}
            per_token_attainable_FLOPS = {"embedding": 0, "attention": 0, "ffn": 0, "lm_head": 0}
            per_token_theoretical_FLOPS = {"embedding": 0, "attention": 0, "ffn": 0, "lm_head": 0}
            
            for i in range(self.num_hidden_layers):
                single_op_operation = self._report_flash_attn_utilization("decode")
                per_token_operations["attention"] += single_op_operation[0]
                per_token_attainable_FLOPS["attention"] += single_op_operation[1]
                per_token_theoretical_FLOPS["attention"] += single_op_operation[2]

                single_op_operation = self._report_ffn_utilization("decode")
                per_token_operations["ffn"] += single_op_operation[0]
                per_token_attainable_FLOPS["ffn"] += single_op_operation[1]
                per_token_theoretical_FLOPS["ffn"] += single_op_operation[2]

            overall_operations["attention"] += per_token_operations["attention"] / (10**9)
            overall_operations["ffn"] += per_token_operations["ffn"] / (10**9)

            overall_attainable_FLOPS["attention"] += per_token_attainable_FLOPS["attention"] / (10**9)
            overall_theoretical_FLOPS["attention"] += per_token_theoretical_FLOPS["attention"] / (10**9)

            overall_attainable_FLOPS["ffn"] += per_token_attainable_FLOPS["ffn"] / (10**9)
            overall_theoretical_FLOPS["ffn"] += per_token_theoretical_FLOPS["ffn"] / (10**9)

        return {
            "operations": overall_operations,
            "attainable_FLOPS": overall_attainable_FLOPS,
            "theoretical_FLOPS": overall_theoretical_FLOPS
        }
    
    def compute_overall_perf(self):
        prefill_perf = self._report_prefill_utilization()
        print(f"Prefill Performance: {prefill_perf}")
        decode_perf = self._report_decode_utilization()
        print(f"Decode Performance: {decode_perf}")
        utilization = (prefill_perf["attainable_FLOPS"]["ffn"] + prefill_perf["attainable_FLOPS"]["attention"] + decode_perf["attainable_FLOPS"]["ffn"] + decode_perf["attainable_FLOPS"]["attention"]) / (prefill_perf["theoretical_FLOPS"]["ffn"] + prefill_perf["theoretical_FLOPS"]["attention"] + decode_perf["theoretical_FLOPS"]["ffn"] + decode_perf["theoretical_FLOPS"]["attention"])
        return utilization