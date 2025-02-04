import json


class model_config:
    def __init__(self, model_param_path):
        model_param = json.load(open(model_param_path))
        self.hidden_size = model_param["hidden_size"]
        self.num_attention_heads = model_param["num_attention_heads"]
        self.num_hidden_layers = model_param["num_hidden_layers"]
        self.intermediate_size = model_param["intermediate_size"]
        self.num_key_value_heads = model_param["num_key_value_heads"]
        self.attention_bias = model_param["attention_bias"]
        self.max_position_embeddings = model_param["max_position_embeddings"]
        self.head_dim = self.hidden_size // self.num_attention_heads
        self.num_head_groups = self.num_attention_heads // self.num_key_value_heads
        self.vocab_size = model_param["vocab_size"]
        self.Tile_Size = 64
        self.DataTypeSize = 8
        self.mvm_tile_size_entry_num = 64 # MVM memory size determined by MVM_MEM_ENTRY_LEN * MLEN * DataTypeSize
        self.mvm_tile_size_entry_num = 64 # SRAM memory size determined by SRAM_MEM_ENTRY_LEN * MLEN * DataTypeSize
        self.theoratical_frequency = 10**9 # 1 GHz


    def rms_layer(self):
        setting_inst_num = 5
        loop_inst_num = 7 + 7 
        loop_num = self.hidden_size // self.Tile_Size 
        instruction_num = 0
        instruction_num += setting_inst_num
        instruction_num += loop_num * loop_inst_num
        return instruction_num

    def projection(self):
        overall_inst_num = 0
    ##Q Projection
        # -- Projection
        setting_inst_num = 9
        mvm_inst_num = 13
        loop_mvm_num = (self.hidden_size // self.Tile_Size) ** 2
        data_transfer_inst_num = 5
        # Load Sin and Cos
        load_cos_sin_inst_num = 5 * (self.head_dim // self.Tile_Size)
        # -- RoPE
        head_setting_inst = self.num_attention_heads * 4
        loop_per_head_inst_num = 16 * (self.head_dim // self.Tile_Size) * self.num_attention_heads
        overall_inst_num += setting_inst_num + mvm_inst_num * loop_mvm_num + data_transfer_inst_num + load_cos_sin_inst_num + head_setting_inst + loop_per_head_inst_num
    ##K Projection
        # -- Projection
        setting_inst_num = 9
        mvm_inst_num = 13
        loop_mvm_num = ((self.num_key_value_heads * self.head_dim) // self.Tile_Size) ** 2
        data_transfer_inst_num = 5
        # Load Sin and Cos
        load_cos_sin_inst_num = 5 * (self.head_dim // self.Tile_Size)
        # -- RoPE
        head_setting_inst = self.num_key_value_heads * 4
        loop_per_head_inst_num = 16 * (self.head_dim // self.Tile_Size) * self.num_key_value_heads
        overall_inst_num += setting_inst_num + mvm_inst_num * loop_mvm_num + data_transfer_inst_num + load_cos_sin_inst_num + head_setting_inst + loop_per_head_inst_num
    ## V Projection
        # -- Projection
        setting_inst_num = 9
        mvm_inst_num = 13
        loop_mvm_num = ((self.num_key_value_heads * self.head_dim) // self.Tile_Size) ** 2
        data_transfer_inst_num = 5
        overall_inst_num += setting_inst_num + mvm_inst_num * loop_mvm_num + data_transfer_inst_num
        return overall_inst_num

    def flash_attention(self):
        overall_inst_num = 0
        # -- Attention
        q_heads = self.num_attention_heads
        settings_in_each_attention = 7
        internel_Tc_Loop = 50 // self.Tile_Size # Assuming 50 for s_kv

        # Internel Tc Loop
        # Q_KT Loop
        Tile_Loop_per_head = self.head_dim // self.Tile_Size
        Q_KT_inst_num = 15 * Tile_Loop_per_head  + 7 * Tile_Loop_per_head # One for QKT another for Vector elementwise qk_scale
        # Row Max
        row_max_inst_num = 7 * Tile_Loop_per_head
        # Reduction by m_new
        reduction_inst_num = 7 * Tile_Loop_per_head
        # Exp
        exp_inst_num = 8 * Tile_Loop_per_head
        # Scalar
        scalar_inst_num = 15
        # Psum
        psum_inst_num = 7 * Tile_Loop_per_head
        # p v
        p_v_inst_num = 23 * Tile_Loop_per_head

        overall_inst_num += q_heads * (settings_in_each_attention + internel_Tc_Loop * (Q_KT_inst_num + row_max_inst_num + reduction_inst_num + exp_inst_num + scalar_inst_num + psum_inst_num + p_v_inst_num))
        return overall_inst_num


    def residual (self):
        overall_inst_num = 0
        # -- Residual
        iteration = self.hidden_size // self.Tile_Size
        overall_inst_num = 10 * iteration
        return overall_inst_num

    def feed_forward(self):
        overall_inst_num = 0
        # -- Feed Forward
        setting_inst_num = 9
        mvm_inst_num = 13
        loop_mvm_num = (self.hidden_size * self.hidden_size) // (self.Tile_Size * self.Tile_Size)
        data_transfer_inst_num = 5
        overall_inst_num = setting_inst_num + (mvm_inst_num + data_transfer_inst_num) * loop_mvm_num
        return overall_inst_num

    def mlp(self):
        overall_inst_num = 0
        # -- MLP
        setting_inst_num = 9
        mvm_inst_num = 13
        loop_mvm_num = (self.hidden_size * self.intermediate_size) // (self.Tile_Size * self.Tile_Size)
        data_transfer_inst_num = 5
        overall_inst_num = setting_inst_num + (mvm_inst_num + data_transfer_inst_num) * loop_mvm_num
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
        overall_inst_num += self.rms_layer()
        overall_inst_num += self.mlp()
        print("Overall instruction number: ", overall_inst_num)
        overall_exe_cycle = overall_inst_num * 3
        theoratical_execution_time = overall_exe_cycle / self.theoratical_frequency
        print("Theoratical execution time: ", theoratical_execution_time)
        return overall_inst_num, theoratical_execution_time


if __name__ == "__main__":
    model = model_config("Model_Lib/llama-3.1-70b.json")
    print(model.compute_overall_inst())






        

