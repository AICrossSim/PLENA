import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from acc_simulator.eval.acc_sim import mxfp_lm_eval

def llm_eval():
    mxfp_lm_eval(
        model_name="meta-llama/Llama-3.1-8B",
        tasks="wikitext",
        preset="XqWqBqKVq",
        preset_mxfp_X="MXFP8_E4M3",
        preset_mxfp_W="MXFP8_E4M3",
        preset_mxfp_Kv="MXFP8_E4M3",
    )
if __name__ == "__main__":
    llm_eval()
