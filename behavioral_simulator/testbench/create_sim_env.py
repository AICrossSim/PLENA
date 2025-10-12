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
    # Store golden_result in a readable format, including tensor contents.
    with open(os.path.join(build_dir, "golden_result.txt"), "w") as f:
        f.write("Golden Result:\n")
        f.write("\nInput Tensor:\n")
        f.write(str(golden_result["input_tensor"].detach().cpu().numpy()))
        f.write("\n\nWeights (state_dict):\n")
        for key, value in golden_result["weights"].items():
            f.write(f"{key}:\n{value.detach().cpu().numpy()}\n")
        f.write("\n\nOriginal Output:\n")
        f.write(str(golden_result["original_output"].detach().cpu().numpy()))