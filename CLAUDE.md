# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PLENA (Programmable Long-context Efficient Neural Accelerator) - custom hardware accelerator for LLM inference with assembly-level programming.

## Build & Test Commands

```bash
# Environment setup (requires nix + direnv)
direnv allow && nix develop
git submodule update --init --recursive

# Run behavioral simulator
just build-behave-sim <task>         # tasks: linear, rms, attn, ffn, bmm
just build-behave-sim-debug <task>   # with memory dumps + visualization

# Re-run existing assembly (no regeneration)
just run-generated-asm               # debug output
just run-generated-asm-quiet         # minimal output (latency/metrics only)

# Hardware & software tests
just test-hw                         # FP unit tests (alias: just th)
just test-sw                         # quantization tests (alias: just ts)

# Compiler
cd compiler && uv run python runner.py compiler <model> <output.asm>
cd compiler && uv run --dev ruff format  # format code
```

## Assembly Pipeline

```
Model Config (doc/Model_Lib/*.json)
    ↓
Python templates (compiler/asm_templates/)
    ↓
Assembly code (.asm)
    ↓
Assembler (tools/assembler/assembly_to_binary.py)
    ↓
Machine code (.mem)
    ↓
Rust simulator (behavioral_simulator/)
    ↓
Accuracy check (behavioral_simulator/testbench/check_mem.py)
```

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `compiler/asm_templates/` | Python functions generating assembly (ffn_asm, flash_attn_asm, etc.) |
| `tools/assembler/` | Assembly → machine code conversion |
| `behavioral_simulator/` | Rust cycle-accurate simulator |
| `behavioral_simulator/testbench/` | Test files (ffn_test.py, attn_test.py, etc.) |
| `doc/Model_Lib/` | Model configs (llama-3.2-1b.json, etc.) |
| `src/definitions/` | ISA (operation.svh), hardware config (configuration.svh) |
| `kernel_agents/` | Anthropic Agent framework for assembly generation |

## Simulator Architecture

The behavioral simulator (`behavioral_simulator/`) is a Rust workspace:
- **runtime**: Core execution engine
- **memory**: On-chip SRAM management
- **ramulator**: HBM memory model integration
- **quantize**: INT8/FP8 precision support

Testbench workflow: Python test generates assembly + input data → Rust simulator executes → Python checks accuracy.

## kernel_agents/ - Anthropic Agent for Assembly Generation

```
kernel_agents/
├── anthropic/
│   ├── agent.py                 # Multi-turn agent with tool calling
│   └── tools/
│       ├── workload.py          # get_workload(model, layer) → dimensions
│       ├── template.py          # get_template(layer) → Python source
│       ├── examples.py          # get_assembly_code_examples() → .asm files
│       ├── doc.py               # get_doc(topic) → ISA/registers/memory
│       ├── machine_code.py      # machine_code_generation(asm) → syntax errors
│       ├── simulator.py         # run_simulator(asm) → latency, accuracy
│       └── instruction_size.py  # get_instruction_size(asm) → count
```

**Agent Design**: Multi-turn, context-efficient (binary data stays on disk). `run_simulator` internally calls `machine_code_generation`.

## Key Files for Reference

- `behavioral_simulator/testbench/ffn_test.py` - Full integration test example
- `compiler/asm_templates/ffn_asm.py` - FFN assembly template
- `tools/assembler/assembly_to_binary.py` - AssemblyToBinary class
- `behavioral_simulator/testbench/check_mem.py` - Accuracy comparison utilities
- `src/definitions/configuration.svh` - Hardware parameters (VLEN, MLEN, BLEN)
- `src/definitions/plena_settings.toml` - Simulator runtime config

## Code Style

- **Python**: Ruff formatter, line-length=120, Python 3.12+
- **RTL**: LowRISC SystemVerilog style guide
- **General**: Concise, sacrifice grammar for brevity
