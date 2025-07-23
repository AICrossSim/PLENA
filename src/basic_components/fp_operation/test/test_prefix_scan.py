import numpy as np
import math
import torch
def hw_fp_adder(exp_a, mant_a, exp_b, mant_b, 
                in_exp_width, in_fix_width, in_fix_frac_width,
                out_exp_width, out_fix_width, out_fix_frac_width):
    """
    Emulates the behavior of the hardware fp_adder module.
    This is a simplified version matching your hardware implementation.
    """
    # Handle the case where one of the inputs is zero (represented as '0 in hardware)
    if mant_a == 0:
        return exp_b, mant_b
    if mant_b == 0:
        return exp_a, mant_a
        
    data_fix_width = out_fix_width - 1
    data_fix_frac_width = out_fix_frac_width

    frac_diff = data_fix_frac_width - in_fix_frac_width
    
    # Step 1: Determine which number has the larger exponent
    if exp_a > exp_b:
        exp_diff = exp_a - exp_b
        mant_a_shifted = mant_a
        mant_b_shifted = mant_b >> exp_diff
        exp_out = exp_a
    else:
        exp_diff = exp_b - exp_a
        mant_b_shifted = mant_b
        mant_a_shifted = mant_a >> exp_diff
        exp_out = exp_b
        
    # Add mantissas (already properly aligned by exponent)
    mant_out = mant_a_shifted + mant_b_shifted
    
    # Normalize if needed
    # Check if mantissa overflowed and needs to be shifted right
    if mant_out >= (1 << (out_fix_width - 1)):
        mant_out = mant_out >> 1
        exp_out += 1
    
    return exp_out, mant_out

def hw_prefix_scan(exp_in, mant_in, 
                  in_exp_width, in_fix_width, in_fix_frac_width, 
                  out_exp_width, out_fix_width, out_fix_frac_width, N = 8):
    """
    Python implementation of the hardware prefix scan module.
    
    Args:
        exp_in: List of input exponents
        mant_in: List of input mantissas
        in_exp_width, in_fix_width, in_fix_frac_width: Input bit widths
        out_exp_width, out_fix_width, out_fix_frac_width: Output bit widths
        
    Returns:
        Lists of output exponents and mantissas
    """
    N = len(exp_in)
    LOGN = math.ceil(math.log2(N))
    
    # Initialize pipeline registers for each stage
    temp_exp = np.zeros((LOGN + 1, N), dtype=np.int32)
    temp_mant = np.zeros((LOGN + 1, N), dtype=np.int32)
    
    # Get data_fix_frac_width from out_fix_frac_width
    data_fix_width = out_fix_width - 1
    data_fix_frac_width = out_fix_frac_width
    
    frac_diff = data_fix_frac_width - in_fix_frac_width
    
    # Input stage - scale mantissa by frac_diff
    for i in range(N):
        temp_mant[0][i] = mant_in[i] << frac_diff
        temp_exp[0][i] = exp_in[i]
    # Input stage
    # for i in range(N):
    #     temp_exp[0][i] = exp_in[i]
    #     temp_mant[0][i] = mant_in[i]
    
    # Process each stage
    for s in range(LOGN):
        # Compute each node in this stage
        stage_exp = np.zeros(N, dtype=np.int32)
        stage_mant = np.zeros(N, dtype=np.int32)
        
        for i in range(N):
            if i >= (1 << s):  # Nodes that receive inputs from previous nodes
                # Get the previous stage inputs
                exp_a = temp_exp[s][i]
                mant_a = temp_mant[s][i]
                exp_b = temp_exp[s][i - (1 << s)]
                mant_b = temp_mant[s][i - (1 << s)]
                
                # Perform addition using the hardware adder model
                stage_exp[i], stage_mant[i] = hw_fp_adder(
                    exp_a, mant_a, exp_b, mant_b,
                    in_exp_width, in_fix_width, in_fix_frac_width,
                    out_exp_width, out_fix_width, out_fix_frac_width
                )
            else:  # Nodes that just pass through their values
                stage_exp[i] = temp_exp[s][i]
                stage_mant[i] = temp_mant[s][i]
        
        # Update pipeline registers for next stage
        for j in range(N):
            temp_exp[s+1][j] = stage_exp[j]
            temp_mant[s+1][j] = stage_mant[j]
    
    # Return output from final stage
    return temp_exp[LOGN].tolist(), temp_mant[LOGN].tolist()

def fp_to_float(exponents, mantissas, frac_diff, q_config):
    """More accurate conversion from fixed-point to float, with factor correction"""
    # Add 3 to the exponent to correct the 8x factor
    return np.array([
        # mantissa * (2.0 ** (-frac_width)) * (2.0 ** (exponent + q_config["IN_FIX_FRAC_WIDTH"]))
        mantissa * (2.0 ** (-frac_diff)) * (2.0 ** exponent)
        for exponent, mantissa in zip(exponents, mantissas)
    ])

# After generating inputs
q_config = {
    "IN_EXP_WIDTH": 4,
    "IN_FIX_WIDTH": 5,
    "IN_FIX_FRAC_WIDTH": 4,
    "OUT_EXP_WIDTH": 5,
    "OUT_FIX_WIDTH": 12,
    "OUT_FIX_FRAC_WIDTH": 8
}

exp_in = np.array([1, 0, 2, 1, 1, 0, 0, 2])
mant_in = np.array([3, 4, 2, 4, 2, 3, 1, 3])
fp_in = torch.tensor([mant_in[i] * 2**exp_in[i] for i in range(len(exp_in))], dtype=torch.float32)
result = torch.cumsum(fp_in, dim=0)
hw_model_exp_out, hw_model_mant_out = hw_prefix_scan(
    exp_in.tolist(), mant_in.tolist(),
    q_config["IN_EXP_WIDTH"], q_config["IN_FIX_WIDTH"], q_config["IN_FIX_FRAC_WIDTH"],
    q_config["OUT_EXP_WIDTH"], q_config["OUT_FIX_WIDTH"], q_config["OUT_FIX_FRAC_WIDTH"]
)
# data_fix_frac_width = out_fix_frac_width
frac_diff = q_config["OUT_FIX_FRAC_WIDTH"] - q_config["IN_FIX_FRAC_WIDTH"]
print("HW model exp:", hw_model_exp_out)
print("HW model mant:", hw_model_mant_out)
print("Expected result:", result.tolist())
print("HW model converted:", 
	  [hw_model_mant_out[i] * 2**hw_model_exp_out[i] for i in range(len(hw_model_exp_out))])
hw_exp, hw_mant = hw_model_exp_out, hw_model_mant_out
corrected = [
    (hw_mant[i] >> frac_diff) * (2 ** hw_exp[i])
    for i in range(len(hw_exp))
]
print("Corrected HW model converted:", corrected)
corrected = [
    ((hw_mant[i] + (1 << (frac_diff-1))) >> frac_diff) * (2**hw_exp[i])
    for i in range(len(hw_exp))
]
print("Corrected HW model converted, rounded:", corrected)
properly_converted = fp_to_float(hw_model_exp_out, hw_model_mant_out, 
                                frac_diff, q_config)
print("Properly converted:", properly_converted)
# breakpoint()