# PLENA Project Instructions

## Environment Setup

**ALWAYS activate conda before running any Python test:**
```bash
source /home/khl22/miniconda3/etc/profile.d/conda.sh && conda activate plena
```

## Running RTL Tests (PLENA_RTL)

RTL tests use cocotb + Verilator. To run from the PLENA_RTL directory:
```bash
source /home/khl22/miniconda3/etc/profile.d/conda.sh && conda activate plena
RTL="$(pwd)" && SIM="${PLENA_SIM:-${RTL}/../PLENA_Simulator}"
PYTHONPATH=${RTL}/tools:${SIM}:${SIM}/tools:${SIM}/compiler python3 <test_script>
```

Key test commands (from PLENA_RTL/justfile):
- `just test-correctness` — SimTop correctness testbench
- `just test-dfc` — data_flow_control unit test

## Running Simulator Tests (PLENA_Simulator)

Use `run.sh` from PLENA_Simulator directory (handles nix+conda):
```bash
bash /home/khl22/new_plena/PLENA_Simulator/run.sh <command>
```

## Project Structure
- `PLENA_RTL/` — SystemVerilog RTL (submodule, branch: rtl/correctness)
- `PLENA_Simulator/` — Python transactional emulator + compiler
- `smollm_ref/` — Reference model weights
