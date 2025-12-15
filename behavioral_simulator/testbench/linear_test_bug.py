import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import nn
from compiler.asm_templates import projection_asm, preload_act_asm, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim
import math



def align64(x):
    return ((x + 63) // 64) * 64


# =============================================================
# Main
# =============================================================
if __name__ == "__main__":

    # ----------------------------
    # Model config
    # ----------------------------
    in_features  = 128
    out_features = 64
    batch_size   = 4

    mlen = 64
    blen = 4
    tile_height = mlen
    fp_preload = [0.0, 1e-6, 1/in_features]

    torch.manual_seed(42)

    act_tensor = torch.randn(batch_size, in_features)
    layer = nn.Linear(in_features, out_features, bias=False)

    weights = layer.weight.data
    original_output = layer(act_tensor)

    print("Original output shape:", original_output.shape)

    # Simulator tensor format: weights stored as (in, out)
    input_tensor = {
        "act_tensor": act_tensor,
        "weights": weights.t(),   # pytorch: (out, in)
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output
    }

    # =============================================================
    # HBM Layout
    # =============================================================
    act_hbm_raw = in_features * batch_size
    weight_hbm_raw = in_features * out_features

    act_hbm_size = align64(act_hbm_raw)
    weight_hbm_size = align64(weight_hbm_raw)

    activation_hbm_offset = 0
    weight_hbm_offset = act_hbm_size
    weight_hbm_end    = weight_hbm_offset + weight_hbm_size

    print("HBM Activation size:", act_hbm_size)
    print("HBM Weight size:", weight_hbm_size)

    assert weight_hbm_offset % 64 == 0
    assert weight_hbm_end    % 64 == 0

    # =============================================================
    # Generate code
    # =============================================================
    code = "; Linear Test\n"
    code += f"; ({batch_size},{in_features}) @ ({in_features},{out_features})\n\n"

    # -------------------------------------------------------------
    # preload weight address registers
    # -------------------------------------------------------------
    code += preload_addr_reg_asm(
        addr_reg_to_set=[1, 2],
        available_registers=[1, 2],
        addr_reg_val=[weight_hbm_offset, weight_hbm_end]
    )
    code += reset_reg_asm([1,2,3])

    # =============================================================
    # VRAM layout
    # =============================================================
    act_vram_base   = 0
    act_vram_stride = align64(in_features)   # VRAM row stride

    print("VRAM Activation stride:", act_vram_stride)

    # result offset must start at next aligned region
    act_rows = (batch_size * act_vram_stride) // 64
    result_vram_offset = act_rows * 64

    print("VRAM result offset:", result_vram_offset)

    # -------------------------------------------------------------
    # Preload Activations
    # -------------------------------------------------------------
    code += preload_act_asm(
        vlen=64,
        preload_len=4,
        batch=batch_size,
        hidden_size=in_features,
        alive_registers=[1,2,3,4,5],
        act_vram_offset=act_vram_base,
        activation_offset_reg=0,
        stride_size=act_vram_stride
    )
    code += reset_reg_asm([1,2,3,4])

    # -------------------------------------------------------------
    # Projection kernel (tile-based write)
    # -------------------------------------------------------------
    code += projection_asm(
        mlen=mlen,
        blen=blen,
        batch=batch_size,     # only used inside compute loop, not for writeback
        hidden_size=in_features,
        out_features=out_features,
        alive_registers=[1,2,3,4,5],
        w_base_hbm_offset_reg=1,
        activation_base_address=act_vram_base,
        result_base_address=result_vram_offset,
        activation_stride=act_vram_stride,
        output_stride=None,        # IMPORTANT: must be None for tile write!
        rope_enabled=False
    )

    # =============================================================
    # VRAM allocation (tile layout)
    # =============================================================
    num_tiles = math.ceil(out_features / blen)    # 4-wide tiles
    result_tile_rows = num_tiles * tile_height    # each tile = 64 rows

    total_vram_rows = act_rows + result_tile_rows

    print("Allocating VRAM rows:", total_vram_rows)

    # =============================================================
    # Write build env
    # =============================================================
    create_sim_env(input_tensor, code, golden_result, fp_preload)
    create_mem_for_sim(
        data_size=total_vram_rows,
        mode="behave_sim",
        asm="linear",
        data=None,
        specified_data_order=["act_tensor", "weights"]
    )

    # =============================================================
    # Comparison parameters
    # =============================================================
    result_start_row = result_vram_offset // 64
    num_rows = result_tile_rows

    comparison_params = {
        "start_row_idx": result_start_row,
        "num_rows": num_rows,
        "num_batches": batch_size,
        "elements_per_batch": out_features,
        "tile_height": tile_height,
        "blen": blen
    }

    build_dir = Path(__file__).parent / "build"
    build_dir.mkdir(exist_ok=True)
    with open(build_dir / "comparison_params.json", "w") as f:
        import json
        json.dump(comparison_params, f, indent=2)

    print("====================================================")
    print("Finished generating fully aligned, tile‑safe assembly")
    print("====================================================\n")