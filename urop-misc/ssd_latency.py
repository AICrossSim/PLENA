import torch
from einops import rearrange # <--- Add this line!
import torch.nn.functional as F
# This is a simplified PyTorch implementation of the Mamba-2 SSD algorithm
# Designed to be ISA-translatable, block-wise, and memory-efficient

# === Parameters ===
batch = 1
length = 512
n_heads = 2
d_head = 4
d_state = 8
block_len = 64
num_chunks = length // block_len
def check_tensor(tensor, name, step_info=""):
    if torch.isnan(tensor).any():
        print(f"!!! NaN detected in {name} {step_info}!!!")
        print(f"Tensor value:\n{tensor}") # Uncomment for full tensor print
        # import pdb; pdb.set_trace() # Uncomment to break execution
    if torch.isinf(tensor).any():
        print(f"!!! Inf detected in {name} {step_info}!!!")
        print(f"Tensor value:\n{tensor}") # Uncomment for full tensor print
        # import pdb; pdb.set_trace() # Uncomment to break execution
#                                                                       HBM
#Sizes for HBM access offsets
size_A = batch * num_chunks * block_len * n_heads
size_B = batch * num_chunks * block_len * n_heads * d_state
size_C = batch * num_chunks * block_len * n_heads * d_state
size_X = batch * num_chunks * block_len * n_heads * d_head
size_Y_diag = size_X
size_Y_off = size_X
size_states = batch * (num_chunks + 1) * n_heads * d_head * d_state
size_A_cs_last = batch * (num_chunks + 1) * n_heads
size_decay_chunk = size_A_cs_last
size_new_states = size_states
size_states_out = batch * (num_chunks) * n_heads * d_head * d_state

#HBM allocation
HBM_SIZE = (
    size_A + size_B + size_C + size_X +
    size_Y_diag + size_Y_off +
    size_states + size_A_cs_last + size_decay_chunk + size_new_states + size_states_out + 100 #100 is a buffer for safety
)
HBM = torch.zeros(HBM_SIZE, dtype=torch.float32)

#Address mapping
offset = 0
HBM_ADDR = {}

def register_hbm(name, size):
    global offset
    HBM_ADDR[name] = offset
    offset += size

register_hbm("A_chunks", size_A)
register_hbm("B_chunks", size_B)
register_hbm("C_chunks", size_C)
register_hbm("X_chunks", size_X)
register_hbm("Y_diag", size_Y_diag)
register_hbm("Y_off", size_Y_off)
register_hbm("states", size_states)
register_hbm("A_cs_last", size_A_cs_last)
register_hbm("decay_chunk", size_decay_chunk)
register_hbm("new_states", size_new_states)
register_hbm("states_out", size_states_out)

print("HBM_SIZE:", HBM_SIZE)
def get_addr(name, b, c, l=0, h=0, d1=0, d2=0):
    base = HBM_ADDR[name]
    if name in ["A_chunks"]:
        return base + ((b * num_chunks + c) * block_len + l) * n_heads + h
    elif name in ["B_chunks", "C_chunks"]:
        return base + (((b * num_chunks + c) * block_len + l) * n_heads + h) * d_state
    elif name in ["X_chunks", "Y_diag", "Y_off"]:
        return base + (((b * num_chunks + c) * block_len + l) * n_heads + h) * d_head
    elif name in ["states", "new_states"]:
        return base + (((b * (num_chunks + 1) + c) * n_heads + h) * d_head + d1) * d_state + d2
    elif name in ["A_cs_last", "decay_chunk"]:
        return base + (b * (num_chunks + 1) + c) * n_heads + h
    elif name in ["states_out"]:
        return base + ((b * num_chunks + c) * n_heads + h) * d_head * d_state + d1 * d_state + d2
    else:
        raise ValueError(f"Unknown tensor name: {name}")

#                                                                                       SRAM
#Matrix SRAM allocation
size_B_cur = block_len * d_state
size_C_cur = block_len * d_state
size_X_cur = block_len * d_head
size_L = block_len * block_len
size_decay_chunk_matrix_inter = (num_chunks + 1) * (num_chunks + 1)
MSRAM_SIZE = (
    size_B_cur + size_C_cur + size_X_cur + size_L +
    size_decay_chunk_matrix_inter)
print("MSRAM_SIZE:", MSRAM_SIZE)
MSRAM = torch.zeros(MSRAM_SIZE, dtype=torch.float32)
#Address mapping for MATRIX SRAM
# MATRIX SRAM layout (2D tensors only)
matrix_sram_offsets = {}
offset = 0

def assign_matrix_sram(name, shape):
    global offset
    size = 1
    for dim in shape:
        size *= dim
    matrix_sram_offsets[name] = {"shape": shape, "offset": offset, "size": size}
    offset += size

assign_matrix_sram("B_cur", (block_len, d_state))         # 64 x 8
assign_matrix_sram("C_cur", (block_len, d_state))         # 64 x 8
assign_matrix_sram("X_cur", (block_len, d_head))          # 64 x 4
assign_matrix_sram("L",     (block_len, block_len))       # 64 x 64
assign_matrix_sram("decay_chunk_matrix_inter", (num_chunks + 1, num_chunks + 1))
def get_addr_matrix(name, l=0, s=0): #l is row index, s is column index
    """Get address in MATRIX SRAM for 2D tensors."""
    if name not in matrix_sram_offsets:
        raise ValueError(f"Unknown matrix tensor name: {name}")
    offset_info = matrix_sram_offsets[name]
    return offset_info["offset"] + (l * offset_info["shape"][1] + s)


#Vector/Scalar SRAM allocation
vsram_offsets = {}
vsram_offset = 0

def assign_vsram(name, size=1):
    global vsram_offset
    vsram_offsets[name] = {"size": size, "offset": vsram_offset}
    vsram_offset += size

# Assign commonly used 1D or scalar variables
assign_vsram("M",               1)
assign_vsram("W",               block_len)
assign_vsram("A_cur",           block_len)
assign_vsram("A_cs",            block_len)
assign_vsram("decay_state",     block_len)
assign_vsram("state_decay_out", block_len)
assign_vsram("scale_factor",    1)
assign_vsram("acc",             1)
assign_vsram("B_val",           1)
assign_vsram("X_val",           1)
assign_vsram("decay",           1)
assign_vsram("matrix_element",  1)
assign_vsram("vector_element",  1)
assign_vsram("Y_diag", d_head)
assign_vsram("Y_off", d_head)
assign_vsram("A_cs_last_cs", num_chunks + 1)  # cumulative sums for inter-chunk scan

VSRAM_SIZE = vsram_offset
print("VSRAM_SIZE:", VSRAM_SIZE)
VSRAM = torch.zeros(VSRAM_SIZE, dtype=torch.float32)

def get_addr_vsram(name, idx=0):
    entry = vsram_offsets[name]
    size = entry["size"]
    offset = entry["offset"]
    assert 0 <= idx < size, f"Index {idx} out of bounds for {name} (size {size})"
    return offset + idx

#R/W operations for HBM, MATRIX SRAM, and VSRAM
def read_hbm(name, *idxs):
    addr = get_addr(name, *idxs)
    return HBM[addr]

def write_hbm(name, *idxs, value):
    addr = get_addr(name, *idxs)
    HBM[addr] = value
def read_matrix(name, l, s):
    addr = get_addr_matrix(name, l, s)
    return MSRAM[addr]

def write_matrix(name, l, s, value):
    addr = get_addr_matrix(name, l, s)
    MSRAM[addr] = value

def read_vsram(name, idx=0):
    addr = get_addr_vsram(name, idx)
    return VSRAM[addr]

def write_vsram(name, idx, value):
    addr = get_addr_vsram(name, idx)
    VSRAM[addr] = value
def load_tensor_to_hbm(tensor, name):
    flat = tensor.flatten()
    base = HBM_ADDR[name]
    HBM[base:base + flat.numel()] = flat
def load_matrix_to_sram(tensor, name):
    """
    Loads a 2D tensor into the correct region of MSRAM.
    tensor: 2D torch tensor
    name: string key registered in matrix_sram_offsets
    """
    assert tensor.ndim == 2, "Only 2D tensors supported for MSRAM"
    info = matrix_sram_offsets[name]
    assert tensor.shape == info["shape"], f"Shape mismatch for {name}: {tensor.shape} vs {info['shape']}"
    flat = tensor.flatten()
    MSRAM[info["offset"]:info["offset"] + flat.numel()] = flat

def read_matrix_from_sram(name):
    """
    Reads a 2D tensor from MSRAM.
    name: string key registered in matrix_sram_offsets
    Returns: 2D torch tensor
    """
    info = matrix_sram_offsets[name]
    flat = MSRAM[info["offset"]:info["offset"] + info["size"]]
    return flat.reshape(info["shape"])
def load_vector_to_vsram(tensor, name):
    """
    Loads a 1D tensor into the correct region of VSRAM.
    tensor: 1D torch tensor
    name: string key registered in vsram_offsets
    """
    assert tensor.ndim == 1, "Only 1D tensors supported for VSRAM"
    info = vsram_offsets[name]
    assert tensor.shape[0] == info["size"], f"Shape mismatch for {name}: {tensor.shape} vs {info['size']}"
    VSRAM[info["offset"]:info["offset"] + info["size"]] = tensor

def read_vector_from_vsram(name):
    """
    Reads a 1D tensor from VSRAM.
    name: string key registered in vsram_offsets
    Returns: 1D torch tensor
    """
    info = vsram_offsets[name]
    return VSRAM[info["offset"]:info["offset"] + info["size"]]
def read_hbm_block(name, b, c, h, block_len):
    # Compute the starting address of A_chunks[b,c,0,h]
    base = get_addr(name, b, c, 0, h)

    # Allocate the output vector
    A_cur = torch.zeros(block_len, dtype=HBM.dtype)

    # the next element of A_cur would be at base + n_heads, not base + 1 so it is necessary to account for this in the stride
    for l in range(block_len):
        addr = base + l * n_heads   # move to A_chunks[b,c,l,h]
        A_cur[l] = HBM[addr]

    return A_cur

def load_flat_to_sram(flat_tensor, name):
    info = matrix_sram_offsets[name]
    assert flat_tensor.numel() == info["size"]
    MSRAM[info["offset"]:info["offset"] + info["size"]] = flat_tensor
def read_hbm_block_B_chunks(name, b, c, h, block_len, d_state):
    B_cur = torch.zeros((block_len, d_state), dtype=HBM.dtype)
    for l in range(block_len):
        base = get_addr(name, b, c, l, h)
        for n in range(d_state):
            B_cur[l, n] = HBM[base + n]
    return B_cur
# === Random Inputs ===
torch.manual_seed(10)
#A = torch.randn(batch, length, n_heads, dtype=torch.float32) * 0.01 #It was necessary to scale down A to avoid infs in matrix L
A = -torch.rand(batch, length, n_heads, dtype=torch.float32) * 4.0  # Uniformly in [-4, 0]
# B = torch.randn(batch, length, n_heads, d_state, dtype=torch.float32)
# C = torch.randn(batch, length, n_heads, d_state, dtype=torch.float32)
B = torch.randn(batch, length, n_heads, d_state, dtype=torch.float32) * 0.5
C = torch.randn(batch, length, n_heads, d_state, dtype=torch.float32) * 0.5
# X = torch.randn(batch, length, n_heads, d_head, dtype=torch.float32)
X = torch.randn(batch, length, n_heads, d_head, dtype=torch.float32) * 0.5
# A.fill_(0)    # so all segsum‑exp weights are 1
# B.fill_(1.0)
# C.fill_(1.0)
# X.fill_(1.0)

# === Reshape into chunks ===
A_chunks = A.reshape(batch, num_chunks, block_len, n_heads)
B_chunks = B.reshape(batch, num_chunks, block_len, n_heads, d_state)
C_chunks = C.reshape(batch, num_chunks, block_len, n_heads, d_state)
X_chunks = X.reshape(batch, num_chunks, block_len, n_heads, d_head)

# === Outputs ===
Y_diag = torch.zeros((batch, num_chunks, block_len, n_heads, d_head), dtype=torch.float32)#, dtype=torch.float32)
Y_off  = torch.zeros_like(Y_diag)

# === State tracking ===
states = torch.zeros((batch, num_chunks + 1, n_heads, d_head, d_state), dtype=torch.float32)
A_cs_last = torch.zeros((batch, num_chunks + 1, n_heads), dtype=torch.float32)  # includes zero prepended
decay_chunk = torch.zeros((batch, num_chunks + 1, n_heads), dtype=torch.float32)
new_states = torch.zeros((batch, num_chunks + 1, n_heads, d_head, d_state), dtype=torch.float32)
M1 = torch.zeros((block_len,), dtype=torch.float32)#, dtype=torch.float32)
W = torch.zeros((block_len,), dtype=torch.float32)#, dtype=torch.float32)


#load into HBM
load_tensor_to_hbm(A_chunks, "A_chunks")
load_tensor_to_hbm(B_chunks, "B_chunks")
load_tensor_to_hbm(C_chunks, "C_chunks")
load_tensor_to_hbm(X_chunks, "X_chunks")
load_tensor_to_hbm(Y_diag, "Y_diag")
load_tensor_to_hbm(Y_off, "Y_off")
load_tensor_to_hbm(states, "states")
load_tensor_to_hbm(A_cs_last, "A_cs_last")
load_tensor_to_hbm(decay_chunk, "decay_chunk")
load_tensor_to_hbm(new_states, "new_states")
# === Helper Functions ===
def cumsum(input_array):  # Shape: (block_len,)
    A_cs = torch.zeros((len(input_array),), dtype=torch.float32)
    total = 0
    for i in range(len(input_array)):
        total += input_array[i]					#
        A_cs[i] = total
    return A_cs

def compute_L(A_cs, T = block_len):
    len_seq = A_cs.size(-1)
    L = torch.zeros((len_seq, len_seq), dtype=torch.float32)
    for i in range(len_seq):
        for j in range(len_seq):  # only compute lower triangle
            if i == j: # Diagonal elements are exp(0) = 1
                L[i, j] = 1.0
            elif i > j: # Lower triangle elements
                sum_diff = A_cs[i] - A_cs[j]
                L[i, j] = torch.exp(sum_diff)
            # else: # i < j (Upper triangle remains 0)
            #write L[i, j] to SRAM
            if T==block_len:
                write_matrix("L", i, j, L[i, j])
            else:
                write_matrix("decay_chunk_matrix_inter", i, j, L[i, j])
    check_tensor(L, "manual_L_from_compute_L_fixed", " (final output)")
    return L
# === Main Loop: Chunk-wise Processing ===    ###This is where execution starts assuming values are already loaded into HBM
for b in range(batch):			#stored in FIX[x0]
    for h in range(n_heads):	#stored in FIX[x1]
        for c in range(num_chunks): #stored in FIX[x2]
            A_cur = read_hbm_block("A_chunks", b, c, h, block_len)
            load_vector_to_vsram(A_cur, "A_cur")
            
            
            B_cur = read_hbm_block_B_chunks("B_chunks", b, c, h, block_len, d_state)
            load_flat_to_sram(B_cur.flatten(), "B_cur")  # Load B_cur into

            
            C_cur = read_hbm_block_B_chunks("C_chunks", b, c, h, block_len, d_state)
            load_flat_to_sram(C_cur.flatten(), "C_cur")  # Load C_cur

            
            X_cur = read_hbm_block_B_chunks("X_chunks", b, c, h, block_len, d_head)
            load_flat_to_sram(X_cur.flatten(), "X_cur")  # Load X_cur

            A_cs = cumsum(A_cur)               # Shape: (block_len,)
            load_vector_to_vsram(A_cs, "A_cs")  # Store cumulative sum in VSRAM

            A_cs_last[b, c + 1, h] = A_cs[-1]  # Save last sum for this chunk
            write_hbm("A_cs_last", b, c + 1, h, value=A_cs_last[b, c + 1, h])  # Store in HBM

            L = compute_L(A_cs)
            L = compute_L(A_cs).flatten()  # Shape: (block_len, block_len)
            load_flat_to_sram(L, "L")  # Store L in MSRAM

            # === Compute Y_diag ===
            for l in range(block_len):
                for s in range(block_len):
        
                    M = torch.dot(C_cur[l], B_cur[s])
                    write_vsram("M", 0, M)  # Store M in VSRAM
                    #scalar M stored in VSRAM
                    W[s] = L[l * block_len + s] * M
                    write_vsram("W", s, W[s])  # Store W[s] in VSRAM
  
                Y_diag[b, c, l, h, :] = torch.mv(X_cur.T, W)
                
                for p in range(d_head):
                    write_hbm("Y_diag", b, c, l, h, p, value=Y_diag[b, c, l, h, p])  # Store Y_diag in HBM, could the elements be written to in parallel?
    
            # === Compute states (before inter-chunk scan) ===
            scale_factor = A_cs[-1]
            write_vsram("scale_factor", 0, scale_factor)  # Store scale_factor in VSRAM
            #store scale_factor in VSRAM
            decay_state = torch.zeros((block_len,), dtype=torch.float32)
            #decay_state = A_cs - scale_factor  # broadcasted operation
            for l in range(block_len):
                decay_state[l] = scale_factor - A_cs[l]     #implement broadcast operation in ISA. it is a bit suspicious here
            decay_state = torch.exp(decay_state) #Vector exponentiation

            for l in range(block_len):
                write_vsram("decay_state", l, decay_state[l])  # Store decay_state in VSRAM, it wouldn't be this explicit in ISA
                #store in VSRAM
            #store in VSRAM
            for p in range(d_head):
                for n in range(d_state):
                    acc = 0
                    for l in range(block_len):
                        B_val = B_chunks[b, c, l, h, n]
                        B_val = read_matrix("B_cur", l, n)  # Load B_cur[l, n] from VSRAM
                        X_val = X_chunks[b, c, l, h, p]
                        X_val = read_matrix("X_cur", l, p)  # Load X_cur[l, p] from VSRAM
                        decay = decay_state[l]
                        temp = B_val * X_val # because ISA operations act on 2 operands
                        acc += temp * decay
                        #store all in VSRAM
                    states[b, c+1, h, p, n] = acc
                    #store in HBM
         
# === Inter-Chunk Scan (new_states = decay_chunk * states) ===
for b in range(batch):
    for h in range(n_heads):
        # 1. Compute cumulative decay across chunks
        A_cs_last_cs = cumsum(A_cs_last[b, :, h])  # Shape: (num_chunks,)
        load_vector_to_vsram(A_cs_last_cs, "A_cs_last_cs")  # Store cumulative sums in VSRAM
        # store this in VSRAM
        decay_chunk_matrix_inter = compute_L(A_cs_last_cs, T=0)  # shape (num_chunks, num_chunks) , I had T=num_chunks but it would be an error if num_chunks = block_len
        load_flat_to_sram(decay_chunk_matrix_inter.flatten(), "decay_chunk_matrix_inter")  # Store in MSRAM
       # store this in MSRAM

        # 2. Apply scan: new_states = dot(decay_chunk, states)
        for z in range(num_chunks + 1):
            for p in range(d_head):
                for n in range(d_state):
                    acc = 0.0
                    # iterate over the 'c_prime' dimension (columns of decay_chunk_matrix_inter, elements of states_slice)
                    for c_prime_idx in range(num_chunks + 1):
                        #store in VSRAM
                        matrix_element = decay_chunk_matrix_inter[z, c_prime_idx]
                        vector_element = states[b, c_prime_idx, h, p, n]
                        acc += matrix_element * vector_element
                    new_states[b, z, h, p, n] = acc
                    write_hbm("new_states", b, z, h, p, n, value=new_states[b, z, h, p, n])  # Store new_states in HBM
                    # val_written = new_states[b, c, h, p, n].item()
                    # write_hbm("new_states", b, c, h, p, n, value=new_states[b, c, h, p, n])
                    # val_read_back = read_hbm("new_states", b, c, h, p, n).item()
                    # print(f"Wrote: {val_written:.6f}, Read back: {val_read_back:.6f}, Diff: {abs(val_written - val_read_back):.6e}")
                                        #write to HBM

# === Final scanned states ===
states_out = new_states[:, :-1, :, :, :] 
    # for each chunk
for b in range(batch):
    for c in range(num_chunks):  # only up to num_chunks
        for h in range(n_heads):
            for p in range(d_head):
                for n in range(d_state):
                    val = states_out[b, c, h, p, n]
                    # compute address manually for states_out
                    base = HBM_ADDR["states_out"]
                    addr = (((b * num_chunks + c) * n_heads + h) * d_head + p) * d_state + n
                    HBM[base + addr] = val
final_state = new_states[:, -1, :, :, :]     # (optional)

# === Compute Y_off ===
for b in range(batch):
    for h in range(n_heads):
        for c in range(num_chunks):
            #load from HBM into VSRAM & MSRAM
            A_cur = A_chunks[b, c, :, h]
            A_cur = read_hbm_block("A_chunks", b, c, h, block_len)
            load_vector_to_vsram(A_cur, "A_cur")
            C_cur = C_chunks[b, c, :, h, :]
            C_cur = read_hbm_block_B_chunks("C_chunks", b, c, h, block_len, d_state)
            load_flat_to_sram(C_cur.flatten(), "C_cur")  # Load C_cur
            A_cs = cumsum(A_cur)
            load_vector_to_vsram(A_cs, "A_cs")  # Store cumulative sum in VSRAM
            #store in VSRAM
            state_decay_out = torch.exp(A_cs)#[:-1])  # shape: (block_len,)
            load_vector_to_vsram(state_decay_out, "state_decay_out")  # Store in VSRAM
            for l in range(block_len):
                for p in range(d_head):
                    acc = 0.0
                    for n in range(d_state):
                        # val_direct = new_states[b, c, h, p, n].item()
                       # val_read = read_hbm("states_out", b, c, h, p, n).item()
                        # print(f"Direct: {val_direct:.6f}, HBM: {val_read:.6f}, Diff: {abs(val_direct - val_read):.6e}")
                        #                         # Load states_out[b, c, h, p, n] from HBM
                        # val_read = read_hbm("states_out", b, c, h, p, n)
                        state_decay_out_val = read_vsram("state_decay_out", l)
                        base = HBM_ADDR["states_out"]
                        addr = (((b * num_chunks + c) * n_heads + h) * d_head + p) * d_state + n
                        val_read = HBM[base + addr].item()
                        temp = val_read * state_decay_out_val
                        acc += (
                            C_cur[l, n] *
                            temp
                        )
                    Y_off[b, c, l, h, p] = acc
                    write_hbm("Y_off", b, c, l, h, p, value=Y_off[b, c, l, h, p])
                    #store in HBM

# === Final Output ===
#go through HBM and add Y_off to corresponding Y_diag, Y_diag would store the final output Y
Y = (Y_diag + Y_off)#.to(torch.float32)
for b in range(batch):
    for c in range(num_chunks):
        for l in range(block_len):
            for h in range(n_heads):
                for p in range(d_head):
                    # Read both values from HBM
                    y_diag_val = read_hbm("Y_diag", b, c, l, h, p)
                    y_off_val = read_hbm("Y_off", b, c, l, h, p)
                    
                    # Add them together
                    y_final = y_diag_val + y_off_val
                    
                    # Store the result back in Y_diag (reusing the same HBM space)
                    write_hbm("Y_diag", b, c, l, h, p, value=y_final)


####end


