h_qkv = 4096                    #Size of the hidden layer  
MLEN = 128                      #Tile size
S_max = 128                     #Maximum number of squence.
DataTypeSize = 8                #Data type size "FP8" Bitwidth
Resource_Utilization = {}

#---- SRAM utilization
SRAM_Resource_Utilization = 0.0

# for MVM (h_qkv * h_qkv * DataTypeSize)
SRAM_Resource_Utilization += h_qkv * h_qkv * DataTypeSize

# for Scratchpad (4 * h_qkv * DataTypeSize)
SRAM_Resource_Utilization += 4 * h_qkv * DataTypeSize

Resource_Utilization["SRAM"] = SRAM_Resource_Utilization/8/1024/1024



# #---- FIFO utilization
# FIFO_Resource_Utilization = 0.0

# # for Q, K, V weight buffer (h_qkv * h_qkv * DataTypeSize)
# FIFO_Resource_Utilization += h_qkv * h_qkv * DataTypeSize

# # for Matrix Machine Write Buffer (h_qkv * DataTypeSize)
# FIFO_Resource_Utilization += h_qkv * DataTypeSize

# Resource_Utilization["FIFO"] = FIFO_Resource_Utilization



#---- RoPE utilization
RoPE_Resource_Utilization = 0.0

# for RoPE (h_qkv * h_qkv * DataTypeSize)
RoPE_Resource_Utilization += h_qkv * DataTypeSize

Resource_Utilization["RoPE"] = RoPE_Resource_Utilization/8/1024/1024