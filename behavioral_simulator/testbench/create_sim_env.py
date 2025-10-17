import os
import torch
import numpy as np


def np_array_to_str_2f(arr):
    arr = np.asarray(arr)
    if arr.ndim == 1:
        return "[" + " ".join([f"{v:.2f}" for v in arr]) + "]"
    elif arr.ndim == 2:
        rows = ["  " + " ".join([f"{v:.2f}" for v in row]) for row in arr]
        return "[\n" + "\n".join(rows) + "\n]"
    else:
        # For higher dimensions, default to numpy's print (rare for this context)
        return np.array2string(arr, formatter={'float_kind':lambda x: "%.2f" % x})

def create_sim_env(input_tensor, input_weight, generated_code, golden_result):
    build_dir = os.path.join(os.path.dirname(__file__), "build")
    os.makedirs(build_dir, exist_ok=True)
    with open(os.path.join(build_dir, "input_tensor.pt"), "wb") as f:
        torch.save(input_tensor, f)
    with open(os.path.join(build_dir, "model_weight.pt"), "wb") as f:
        torch.save(input_weight, f)
    with open(os.path.join(build_dir, "generated_asm_code.asm"), "w") as f:
        f.write(generated_code)
    # Store golden_result in a readable format, including tensor contents.

    with open(os.path.join(build_dir, "golden_result.txt"), "w") as f:
        f.write("Golden Result:\n")
        f.write("\nInput Tensor:\n")
        f.write(np_array_to_str_2f(golden_result["input_tensor"].detach().cpu().numpy()))
        f.write("\n\nWeights (state_dict):\n")
        for key, value in golden_result["weights"].items():
            f.write(f"{key}:\n{np_array_to_str_2f(value.detach().cpu().numpy())}\n")
        f.write("\n\nOriginal Output:\n")
        f.write(np_array_to_str_2f(golden_result["original_output"].detach().cpu().numpy()))