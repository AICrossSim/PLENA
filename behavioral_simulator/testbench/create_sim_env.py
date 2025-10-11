import os
import torch

def create_sim_env(input_tensor, input_weight, generated_code, golden_result):
    build_dir = os.path.join(os.path.dirname(__file__), "build")
    os.makedirs(build_dir, exist_ok=True)
    with open(os.path.join(build_dir, "input_tensor.pt"), "wb") as f:
        torch.save(input_tensor, f)
    with open(os.path.join(build_dir, "model_weight.pt"), "wb") as f:
        torch.save(input_weight, f)
    with open(os.path.join(build_dir, "generated_asm_code.asm"), "w") as f:
        f.write(generated_code)
    with open(os.path.join(build_dir, "golden_result.txt"), "w") as f:
        f.write(str(golden_result))