import torch
from einops import rearrange # <--- Add this line!
import torch.nn.functional as F

# test commit

def check_tensor(tensor, name, step_info=""):
    if torch.isnan(tensor).any():
        print(f"!!! NaN detected in {name} {step_info}!!!")
        print(f"Tensor value:\n{tensor}") # Uncomment for full tensor print
        # import pdb; pdb.set_trace() # Uncomment to break execution
    if torch.isinf(tensor).any():
        print(f"!!! Inf detected in {name} {step_info}!!!")
        print(f"Tensor value:\n{tensor}") # Uncomment for full tensor print
        # import pdb; pdb.set_trace() # Uncomment to break execution
def segsum(x):
	"""Naive segment sum calculation. exp(segsum(A)) produces a 1-SS matrix,
	which is equivalent to a scalar SSM."""
	T = x.size(-1)
	x_cumsum = torch.cumsum(x, dim=-1)
	check_tensor(x_cumsum, "x_cumsum", " (in ssd.segsum)") # ADDED
	x_segsum = x_cumsum[..., :, None] - x_cumsum[..., None, :]
	mask = torch.tril(torch.ones(T, T, device=x.device, dtype=bool), diagonal=0)
	x_segsum = x_segsum.masked_fill(~mask, -torch.inf)
	#check_tensor(x_segsum, "x_segsum (after mask)", " (in ssd.segsum)") # ADDED
	return x_segsum
def ssd(X, A, B, C, block_len=64, initial_states=None):
	"""
	Arguments:
	X: (batch, length, n_heads, d_head)
	A: (batch, length, n_heads)
	B: (batch, length, n_heads, d_state)
	C: (batch, length, n_heads, d_state)
	Return:
	Y: (batch, length, n_heads, d_head)
	"""
	assert X.dtype == A.dtype == B.dtype == C.dtype
	assert X.shape[1] % block_len == 0
	# Rearrange into blocks/chunks
	X, A, B, C = [rearrange(x, "b (c l) ... -> b c l ...", l=block_len) for x in (X, A, B, C)]
	A = rearrange(A, "b c l h -> b h c l")
	A_cumsum = torch.cumsum(A, dim=-1)
	# 1. Compute the output for each intra-chunk (diagonal blocks)
	L = torch.exp(segsum(A))
	Y_diag = torch.einsum("bclhn,bcshn,bhcls,bcshp->bclhp", C, B, L, X)
	# 2. Compute the state for each intra-chunk
	# (right term of low-rank factorization of off-diagonal blocks; B terms)
	decay_states = torch.exp((A_cumsum[:, :, :, -1:] - A_cumsum))
	states = torch.einsum("bclhn,bhcl,bclhp->bchpn", B, decay_states, X)
	# 3. Compute the inter-chunk SSM recurrence; produces correct SSM states at chunk boundaries
	# (middle term of factorization of off-diag blocks; A terms)
	if initial_states is None:
		initial_states = torch.zeros_like(states[:, :1])
	states = torch.cat([initial_states, states], dim=1)
	decay_chunk = torch.exp(segsum(F.pad(A_cumsum[:, :, :, -1], (1, 0))))
	new_states = torch.einsum("bhzc,bchpn->bzhpn", decay_chunk, states)
	states, final_state = new_states[:, :-1], new_states[:, -1]
	# 4. Compute state -> output conversion per chunk
	# (left term of low-rank factorization of off-diagonal blocks; C terms)
	state_decay_out = torch.exp(A_cumsum)
	Y_off = torch.einsum('bclhn,bchpn,bhcl->bclhp', C, states, state_decay_out)
	# Add output of intra-chunk and inter-chunk terms (diagonal and off-diagonal blocks)
	Y = rearrange(Y_diag+Y_off, "b c l h p -> b (c l) h p")
	return Y, final_state
import torch

# This is a simplified PyTorch implementation of the Mamba-2 SSD algorithm
# Designed to be ISA-translatable, block-wise, and memory-efficient

# === Parameters ===
batch = 4
length = 512
n_heads = 2
d_head = 4
d_state = 8
block_len = 64
num_chunks = length // block_len

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



# === Helper Functions ===
def cumsum(input_array):  # Shape: (block_len,)
    A_cs = torch.zeros((len(input_array),), dtype=torch.float32)
    total = 0
    for i in range(len(input_array)):
        total += input_array[i]
        A_cs[i] = total
    return A_cs
def compute_L(A_cs, T=block_len):
    len_seq = A_cs.size(-1)
    
    # Initialize result matrix
    L = torch.zeros((len_seq, len_seq), dtype=torch.float32)
    
    # Set diagonal to 1.0 first
    L.fill_diagonal_(1.0)
    
    # For each shift amount (1, 2, 3, ..., len_seq-1)
    for shift in range(1, len_seq):
        # Shift A_cs by 'shift' positions to the right with zero padding
        shifted_A_cs = torch.zeros_like(A_cs)
        shifted_A_cs[shift:] = A_cs[:-shift]
        
        # Compute difference: A_cs - shifted_A_cs
        diff = A_cs - shifted_A_cs
        
        # Create mask for this shift
        # For shift=1: [0, 1, 1, 1, ..., 1] (all except first element)
        # For shift=2: [0, 0, 1, 1, ..., 1] (all except first two elements)
        # For shift=k: [0, 0, ..., 0, 1, 1, ..., 1] (zeros for first k elements)
        mask = torch.zeros(len_seq, dtype=torch.float32)
        mask[shift:] = 1.0
        
        # Apply mask and exponentiate
        exp_masked = torch.exp(diff) * mask  # Ensure zeros stay zeros
        #print(f"Shift={shift}, exp_masked={exp_masked}")
        # Add to result matrix at the appropriate diagonal
        # For shift=1, this goes to the 1st subdiagonal
        # For shift=2, this goes to the 2nd subdiagonal
        for i in range(shift, len_seq):
            L[i, i-shift] = exp_masked[i]
            #print(f"Setting L[{i}, {i-shift}] = exp({A_cs[i]} - {A_cs[i-shift]}) = {exp_masked[i].item()}")
            #print(len(exp_masked))
        # for i in range(len_seq):
        #     L[i] = exp_masked

    
    return L




def compute_L_packed(A_cs):
    T = A_cs.numel()
    L_bands = torch.zeros((T, T), dtype=torch.float32)
    L_bands[0].fill_(1.0)  # main diagonal
    for k in range(1, T):
        shifted = torch.zeros_like(A_cs)
        shifted[k:] = A_cs[:-k]
        diff = A_cs - shifted
        exp_masked = torch.exp(diff)      # first k entries can be left as 0 (ignored)
        L_bands[k] = exp_masked           # row k holds the k-th subdiagonal as a vector
    return L_bands

# def banded_apply_LM(L_bands: torch.Tensor, M: torch.Tensor, X: torch.Tensor) -> torch.Tensor:
#     """
#     Compute Y = (L ⊙ M) @ X using banded L (packed subdiagonals), dense M and X.
#     L_bands: (T, T), L_bands[k, k:] = L[i, i-k] for i>=k (else 0)
#     M: (T, T) dense
#     X: (T, d)
#     Returns Y: (T, d)
#     """
#     T, d = X.shape
#     Y = torch.zeros((T, d), dtype=X.dtype, device=X.device)
#     # k = 0 (main diagonal): Y += diag(M) * X
#     diag0 = torch.diagonal(M, offset=0)          # (T,)
#     Y += diag0[:, None] * X
#     # k >= 1: accumulate subdiagonals
#     for k in range(1, T):
#         mk = torch.diagonal(M, offset=-k)        # (T-k,)
#         lk = L_bands[k, k:]                      # (T-k,)
#         coeff = mk * lk                          # (T-k,)
#         Y[k:, :] += coeff[:, None] * X[:T-k, :]
#     return Y

def banded_apply_L(L_bands: torch.Tensor, X: torch.Tensor) -> torch.Tensor:
    T, D = X.shape
    Y = X.clone()                     # diag(L)=1
    for k in range(1, T):
        coeff = L_bands[k, k:]        # (T-k,)
        Y[k:, :] += coeff[:, None] * X[:T-k, :]
    return Y

def apply_LM_uv(A_cs: torch.Tensor, M: torch.Tensor, X: torch.Tensor) -> torch.Tensor:
    """
    Y = (L ⊙ M) @ X without scanning M diagonals.
    u = exp(A_cs), v = exp(-A_cs); Y = diag(u) @ [ tril(M) @ (diag(v) @ X) ].
    Shapes: A_cs (T,), M (T,T), X (T,d) -> Y (T,d)
    """
    u = torch.exp(A_cs)                 # (T,)
    v = torch.exp(-A_cs)                # (T,)
    Z = v[:, None] * X                  # diag(v) @ X, (T,d)
    M_lower = torch.tril(M)             # zero upper triangle, (T,T)
    Y_mid = M_lower @ Z                 # (T,d)
    Y = u[:, None] * Y_mid              # diag(u) @ Y_mid
    return Y
# === Main Loop: Chunk-wise Processing ===    ###This is where execution starts assuming values are already loaded into HBM
for b in range(batch):
    for h in range(n_heads):
        for c in range(num_chunks):
            A_cur = A_chunks[b, c, :, h]#.to(torch.float32)  # (block_len,)
 
            B_cur = B_chunks[b, c, :, h, :]#.to(torch.float32)  # (block_len, d_state)

            C_cur = C_chunks[b, c, :, h, :]#.to(torch.float32)  # (block_len, d_state)
   
            X_cur = X_chunks[b, c, :, h, :]#.to(torch.float32)  # (block_len, d_head)

            A_cs = cumsum(A_cur)               # Shape: (block_len,)
            A_cs_last[b, c + 1, h] = A_cs[-1]  # Save last sum for this chunk
            #A_cs[-1] is reduction sum if element_wise access is not possible
            # L = compute_L(A_cs)  # (block_len, block_len)
            # #L_bands = compute_L_packed(A_cs)  # (block_len, block_len)
            # # === Compute Y_diag (vectorized over s for each l) ===
            # M = torch.matmul(C_cur, B_cur.T)            # shape (block_len, block_len)

            # # Weight by L
            # W = L * M                               # shape (block_len, block_len)            # Multiply each row of W_all with X_cur
            # Y_diag[b, c, :, h, :] = torch.matmul(W, X_cur)  # (block_len, d_head)
            # === Compute states (before inter-chunk scan), vectorized ===
            # broadcast subtraction and exponentiation
            decay_state = torch.exp(A_cs[-1] - A_cs)                # (block_len,)
            L_bands = compute_L_packed(A_cs)               # (T, T)
            M = torch.matmul(C_cur, B_cur.T)               # (T, T)
            Y_diag[b, c, :, h, :] = apply_LM_uv(A_cs, M, X_cur)            
            X_weighted = X_cur.T * decay_state#.unsqueeze(1)           # (block_len, d_head)
            states[b, c+1, h] = torch.matmul(X_weighted, B_cur)               # (d_head, d_state)
         
# === Inter-Chunk Scan (new_states = decay_chunk * states) ===
for b in range(batch):
    for h in range(n_heads):
        #load vector A_cs_last[b, :, h] and compute cumulative sum
        A_cs_last_cs = cumsum(A_cs_last[b, :, h])
        #compute L based on this matrix                                   #
        # decay_chunk_matrix_inter = compute_L(A_cs_last_cs)                     #
        # S = states[b, :, h]                  # (Z, d_head, d_state)
        # NS = torch.empty_like(S)             # (Z, d_head, d_state)
        # for p in range(d_head):
        #     NS[:, p, :] = torch.matmul(decay_chunk_matrix_inter, S[:, p, :])  # (Z, d_state)
        # new_states[b, :, h] = NS
        L_bands_inter = compute_L_packed(A_cs_last_cs)            # (Z+1, Z+1)
        S  = states[b, :, h]                                      # (Z+1, d_head, d_state)
        NS = torch.empty_like(S)
        for p in range(d_head):
            NS[:, p, :] = banded_apply_L(L_bands_inter, S[:, p, :])  # (Z+1, d_state)
        new_states[b, :, h] = NS

# === Final scanned states ===
states_out = new_states[:, :-1, :, :, :]                                            # (batch, num_chunks, n_heads, d_head, d_state)
final_state = new_states[:, -1, :, :, :]

# === Compute Y_off (vectorized per chunk) ===
for b in range(batch):
    for h in range(n_heads):
        for c in range(num_chunks):
            A_cur = A_chunks[b, c, :, h]                                            # (block_len,)
            C_cur = C_chunks[b, c, :, h, :]                                         # (block_len, d_state)
            S_chunk = states_out[b, c, h]                                           # (d_head, d_state)

            # state_decay_out[l] = exp(A_cs[l])
            A_cs = cumsum(A_cur)
            state_decay_out = torch.exp(A_cs)                                        # (block_len,)

            # For all l at once:
            # temp = (d_head, d_state) @ (d_state, block_len) -> (d_head, block_len)
            temp = torch.matmul(S_chunk, C_cur.T)  # (block_len, d_head)
            # Scale each row l by state_decay_out[l], then transpose -> (block_len, d_head)
            Y_off_block = temp * state_decay_out#.unsqueeze(1)
            Y_off[b, c, :, h, :] = Y_off_block.T

# === Final Output ===
Y = Y_diag + Y_off

# === Final Output (vectorized with explicit shapes) ===
for b in range(batch):
    for c in range(num_chunks):
        for l in range(block_len):
            for h in range(n_heads):
                # Vectorized addition for the entire d_head dimension
                Y_diag_vec = Y_diag[b, c, l, h, :]  # Shape: (d_head,)
                Y_off_vec = Y_off[b, c, l, h, :]    # Shape
                
                # Vectorized addition
                Y_final_vec = Y_diag_vec + Y_off_vec
                
                # Write back entire vector
                Y[b, c, l, h, :] = Y_final_vec

####end


##Verification with reference implementation
Y_torch, final_state_torch = ssd(
    torch.tensor(X, dtype=torch.float32),
    torch.tensor(A, dtype=torch.float32),
    torch.tensor(B, dtype=torch.float32),
    torch.tensor(C, dtype=torch.float32),
    block_len=block_len
)
#compute A, B, C from X, delta
#try all 1s
Y_reshaped =  Y.reshape(batch, num_chunks * block_len, n_heads, d_head)
Y_torch_np = Y_torch.detach().numpy()
# Find the index of the largest absolute difference using PyTorch
diff = torch.abs(Y_reshaped - Y_torch)
max_diff = torch.max(diff)
idx = torch.nonzero(diff == max_diff, as_tuple=True)

if idx[0].numel() > 0:
    # Take the first occurrence
    first_idx = tuple(i[0].item() for i in idx)
    print("Biggest mismatch at index:", first_idx)
    print("Y_reshaped value:", Y_reshaped[first_idx].item())
    print("Y_torch value:", Y_torch[first_idx].item())
    print("Absolute difference:", diff[first_idx].item())
else:
    print("No mismatches found.")

diff = (Y_reshaped - Y_torch).reshape(-1)      # flatten the tensor
l2_norm = torch.norm(diff, p=2).item()  # Euclidean norm
print(f"L2 norm of the error: {l2_norm:.4f}")


_, torch_states = ssd(X, A, B, C, block_len)
print("Max abs diff in final_state:", torch.max(torch.abs(torch_states - final_state)))
chunk_errors = []
for c in range(num_chunks):
    diff_chunk = Y_reshaped[:, c*block_len:(c+1)*block_len] - Y_torch[:, c*block_len:(c+1)*block_len]
    chunk_errors.append(torch.norm(diff_chunk).item())

# import matplotlib.pyplot as plt
# plt.plot(chunk_errors)
# plt.xlabel("Chunk")
# plt.ylabel("Chunk error norm")
# plt.title("Error accumulation across chunks")
# plt.show()
Y_diag_torch = Y_torch.reshape(batch, num_chunks, block_len, n_heads, d_head) - Y_off
diag_diff = torch.abs(Y_diag - Y_diag_torch)
max_diag_diff = torch.max(diag_diff)
print("Y_diag max abs diff:", max_diag_diff.item())
Y_off_torch = Y_torch.reshape(batch, num_chunks, block_len, n_heads, d_head) - Y_diag
off_diff = torch.abs(Y_off - Y_off_torch)
max_off_diff = torch.max(off_diff)
print("Y_off max abs diff:", max_off_diff.item())