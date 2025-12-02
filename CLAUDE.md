# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PLENA (Programmable Long-context Efficient Neural Accelerator) is a specialized hardware accelerator for long-context LLM inference. The project consists of four main components that work together:

```
HuggingFace Model
       ↓
   [Compiler] (Python) → Assembly (.asm) → Machine Code (.mem)
       ↓
   [Behavioral Simulator] (Rust) ← HBM data (.bin)
       ↓
   [RTL/Hardware] (SystemVerilog) ← Configuration from src/definitions/
       ↓
   [Acc Simulator] (Python) ← Accuracy/quantization analysis
```

## Common Commands

### Environment Setup
```bash
direnv allow
nix develop
git submodule update --init --recursive
```

### Behavioral Simulation
```bash
# Run behavioral simulator (release mode)
just build-behave-sim linear    # Tasks: linear, rms, attn, ffn, bmm, two_input, s_map_v, dllm1

# Debug mode with verbose output
just build-behave-sim-debug linear

# Re-run without rebuilding testbench
just run-generated-asm
```

### Compiler
```bash
cd compiler
just run                        # Compiles unsloth/Meta-Llama-3.1-8B to test_output.asm
just format                     # Format with ruff

# Direct usage
uv run python runner.py compiler <model_path> <output.asm>
```

### Hardware Tests
```bash
just test-hw                    # RTL testbenches (cocotb/Python)
just test-sw                    # Software/quantization tests
```

### Acc Simulator
```bash
conda env create -f acc_simulator/environment.yml
conda activate acc-sim
bash acc_simulator/run_acc_sim_job.sh
```

### Formatting
```bash
just reformat                   # Black formatter for Python
```

## Architecture

### Directory Structure
- `src/` - SystemVerilog RTL (hardware design)
  - `definitions/` - Hardware config (`configuration.svh`, `precision.svh`, `plena_settings.toml`)
  - `basic_components/` - FP operations, memory units
  - `system/` - Top-level system integration
- `behavioral_simulator/` - Rust cycle-accurate simulator
  - `src/` - Main simulator code
  - `lib/` - Workspace crates (runtime, memory, ramulator, quantize, buddy)
  - `testbench/` - Python test generators (produces `.mem` and `.bin` files)
- `compiler/` - Python compiler (HuggingFace → PLENA assembly)
  - `parser/` - Model and hardware parsing
  - `scheduler/` - Memory layout and register allocation
  - `passes/` - Code generation passes
  - `asm_templates/` - Operation-specific assembly generators
- `acc_simulator/` - Python accuracy simulator for quantization analysis
- `tools/` - Utilities (assembler, quantization tools, Synopsys scripts)
- `test/` - RTL-level testbenches

### Compiler Pipeline
1. **Model Parsing** (`llm_parser.py`) - Extract HuggingFace model → symbolic graph
2. **Hardware Parsing** (`hardware_parser.py`) - Read `.svh` constraints
3. **Scheduling** (`scheduler.py`) - Memory layout + register allocation
4. **Code Generation** (`code_gen.py` + `asm_templates/`) - Generate assembly

### Behavioral Simulator Flow
1. Python testbench generates: `generated_machine_code.mem` (hex opcodes) + `hbm_for_behave_sim.bin` (weights/activations)
2. Rust simulator executes with cycle-accurate HBM timing (via Ramulator)
3. `view_mem.py` compares output against golden values

### Key Configuration Files
- `src/definitions/configuration.svh` - Hardware dimensions (MLEN, BLEN, VLEN, SRAM sizes)
- `src/definitions/precision.svh` - Data types (FP formats, MX block sizes)
- `behavioral_simulator/src/definitions/plena_settings.toml` - Simulator config (latencies, precision)
- `compiler/scheduler/mem_layout_lib.json` - Memory layout templates
- `compiler/scheduler/reg_assignment_lib.json` - Register allocation rules

## Hardware Architecture (PLENA)

- **Matrix Machine**: Matrix-matrix/matrix-vector multiplies (M_MM, M_TMM, M_BMM, M_MV)
- **Vector Machine**: Element-wise ops (V_ADD, V_MUL, V_EXP, V_RED_SUM, V_RED_MAX)
- **Scalar Unit**: FP/INT scalar operations
- **HBM Controller**: Prefetch/store with realistic timing (H_PREFETCH_M, H_PREFETCH_V, H_STORE_V)

Tile sizes: MLEN=64, VLEN=64, BLEN=4 (configurable in `configuration.svh`)

## Code Style
- SystemVerilog: [LowRISC style guide](https://github.com/lowRISC/style-guides)
- Python: Black formatter (`just reformat`)
- Rust: Standard rustfmt

## Hardware-Software Co-Design Exploration (Dec 2024)

### Task
Optimize the linear layer assembly code generation (`compiler/asm_templates/projection_asm.py`) for latency while maintaining MSE < 1.0. Explore hardware configurations (MLEN, BLEN) jointly with compiler optimizations.

### Files Created/Modified
- `compiler/asm_templates/projection_asm.py` - Optimized assembly generator (reduced 374→297 instructions)
- `behavioral_simulator/testbench/config_search.py` - Hardware configuration search script
- `behavioral_simulator/testbench/codesign_search.py` - Joint HW-SW co-design exploration

### Key Findings

#### 1. Assembly Code Optimization (Linear Layer)

**Operation**: `(Batch, Hidden) @ (Hidden, Hidden) -> (Batch, Hidden)` matrix multiplication

**Original vs Optimized**:
| Metric | Original | Optimized | Improvement |
|--------|----------|-----------|-------------|
| Latency | 5013ns | 4943ns | 1.4% |
| Instructions | 374 | 297 | 20.6% |
| MSE | 0.534 | 0.507 | 5% better |

**Optimization Techniques Applied** (applicable to other layers):

1. **Dead Code Elimination**
   - Remove register updates after their last use in a loop iteration
   - Example: Don't update `act_reg` after the last M_MM in inner loop
   ```python
   # Before: Always update
   for j in range(num_weight_tiles):
       lines.append(f"M_MM 0, gp{w_sram_reg}, gp{act_reg}")
       lines.append(f"S_ADDI_INT gp{w_sram_reg}, ...")  # Always
   # After: Skip on last iteration
   if j < num_weight_tiles - 1:
       lines.append(f"S_ADDI_INT gp{w_sram_reg}, ...")
   ```

2. **Incremental vs Absolute Addressing**
   - Use `S_ADDI_INT gp{reg}, gp{reg}, offset` (increment) instead of `S_ADDI_INT gp{reg}, gp0, absolute`
   - Saves instructions when addresses follow predictable patterns
   - Trade-off: Incremental creates dependencies; absolute allows parallel execution

3. **Register Reuse**
   - Minimize redundant `reset_reg_asm()` calls between phases
   - Track which registers are "live" and only reset when necessary

4. **Prefetch Grouping by MLEN Block**
   - Group all weight prefetches for an MLEN block together
   - Reduces address register setup overhead
   - Structure: `[Prefetch Block] -> [Compute tiles_per_mlen times] -> [Next Block]`

5. **Loop Structure Optimization**
   - Current: Fully unrolled (best for small tile counts)
   - For larger layers: Consider partial unrolling or loop constructs if ISA supports

**Code Structure for Linear Layer** (`projection_asm.py`):
```
; Setup phase (4 instructions)
S_ADDI_INT gp{act_reg}, gp0, {scale}
C_SET_SCALE_REG gp{act_reg}
S_ADDI_INT gp{act_reg}, gp0, {stride}
C_SET_STRIDE_REG gp{act_reg}

; For each output tile:
;   If new MLEN block: Prefetch all weights for this block
;   Set weight SRAM offset
;   For each weight tile: M_MM (accumulate)
;   M_MM_WO (write output)
;   Reset activation pointer (skip on last tile)
```

**Generalizing to Other Layers**:
- **Attention (attn)**: Similar tiled structure, but needs Q/K/V projections + softmax + output projection
- **FFN**: Two linear layers with activation in between
- **RMSNorm**: Vector operations (V_RED_SUM, V_MUL) - focus on reducing vector op overhead
- **BMM (Batched MatMul)**: Same optimizations apply, different loop bounds

**Key Insight**: Latency is dominated by M_MM operations. Scalar instruction optimizations reduce code size but have minimal latency impact. Focus optimization effort on:
1. Reducing number of M_MM operations (via better tiling)
2. Overlapping prefetch with compute (if HW supports)
3. Maximizing BLEN (batch size) for better utilization

#### 2. BLEN (Batch Size) Impact - **Major Performance Lever**
| BLEN | Latency (ns) | Instructions | Speedup |
|------|--------------|--------------|---------|
| 4    | 4943         | 297          | 1.0x    |
| 8    | 2810         | 169          | 1.76x   |
| 16   | 1749         | 105          | 2.83x   |
| 32   | 1198         | 73           | 4.13x   |

**Conclusion**: Increasing BLEN provides near-linear speedup (4x for BLEN=32 vs BLEN=4)

#### 3. MLEN Impact - **Simulator Constraint**
Only MLEN=64 works with the current behavioral simulator. Other values (8, 16, 32, 128) fail due to hardcoded tensor dimensions in the Rust simulator.

Error: `start (64) + length (4) exceeds dimension size (64)`

#### 4. Compiler Strategy Impact - **Minimal Effect**
Different prefetch strategies (per_mlen_block, all_upfront, interleaved) produce identical latency because:
- Latency is dominated by M_MM (matrix multiply) operations
- Scalar/address instructions have negligible latency
- All strategies perform the same number of M_MM operations

### Recommendations
1. **For latency optimization**: Increase BLEN (batch size) - this is the primary performance lever
2. **Compiler strategy**: Use `per_mlen+full_unroll` (default) - cleaner code, same performance
3. **To enable MLEN exploration**: Parameterize the Rust simulator to read MLEN from config

### Running Co-Design Search
```bash
cd behavioral_simulator/testbench
python3 codesign_search.py  # Runs HW-SW co-design exploration
python3 config_search.py    # Runs hardware config search only
```
