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
        self.mlp_bias = model_param["mlp_bias"]
        self.head_dim = self.hidden_size // self.num_attention_heads
        self.num_head_groups = self.num_attention_heads // self.num_key_value_heads
        self.vocab_size = model_param["vocab_size"]
        self.Tile_Size = 64
        self.DataTypeSize = 8
        self.mvm_tile_size_entry_num = 64 # MVM memory size determined by MVM_MEM_ENTRY_LEN * MLEN * DataTypeSize
        self.mvm_tile_size_entry_num = 64 # SRAM memory size determined by SRAM_MEM_ENTRY_LEN * MLEN * DataTypeSize
        


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
        loop_mvm_num = (self.hidden_size // self.Tile_Size) ^ 2
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
        loop_mvm_num = (self.num_key_value_heads * self.head_dim // self.Tile_Size) ^ 2
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
        loop_mvm_num = (self.num_key_value_heads * self.head_dim // self.Tile_Size) ^ 2
        data_transfer_inst_num = 5
        overall_inst_num += setting_inst_num + mvm_inst_num * loop_mvm_num + data_transfer_inst_num
        return overall_inst_num











        

