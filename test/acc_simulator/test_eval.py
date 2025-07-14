import sys
import os

import torch
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from acc_simulator.eval.acc_sim import mxfp_lm_eval

def llm_eval():
    torch.manual_seed(0)
    mxfp_lm_eval(
        model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        tasks="wikitext",
        preset="XqWqBqKVq",
        preset_mxfp_X="MXFP8_E4M3",
        preset_mxfp_W="MXFP8_E4M3",
        preset_mxfp_Kv="MXFP8_E4M3",
        preset_minifloat="FP8_E4M3",
    )
if __name__ == "__main__":
    llm_eval()
