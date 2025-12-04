# CLAUDE.md

## Project Overview

PLENA LLM Accelerator - custom hardware accelerator for LLM inference with assembly-level programming.

## Assembly Pipeline

```
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
| `compiler/asm_templates/` | Python functions that generate assembly (ffn_asm, flash_attn_asm, etc.) |
| `tools/assembler/` | Assembly → machine code conversion |
| `behavioral_simulator/` | Rust-based cycle-accurate simulator |
| `behavioral_simulator/testbench/` | Test files (ffn_test.py, attn_test.py, etc.) |
| `doc/Model_Lib/` | Model configs (llama-3.2-1b.json, etc.) |
| `src/definitions/` | ISA (operation.svh), hardware config (configuration.svh) |

## kernel_agents/ - Anthropic Agent for Assembly Generation

```
kernel_agents/
├── README.md
└── anthropic/
    ├── agent.py                 # Multi-turn agent with tool calling
    └── tools/
        ├── workload.py          # get_workload(model, layer) → dimensions
        ├── template.py          # get_template(layer) → Python source
        ├── examples.py          # get_assembly_code_examples() → .asm files
        ├── doc.py               # get_doc(topic) → ISA/registers/memory
        ├── machine_code.py      # machine_code_generation(asm) → syntax errors
        ├── simulator.py         # run_simulator(asm) → latency, accuracy
        └── instruction_size.py  # get_instruction_size(asm) → count
```

### Agent Design

- **Multi-turn**: Messages append each iteration, Claude sees full history
- **Context-efficient**: Binary data stays on disk, only errors/metrics returned to Claude
- **Tool flow**: `run_simulator` internally calls `machine_code_generation`, so one tool does full pipeline

### Usage

```python
from kernel_agents.anthropic import AnthropicAgent

agent = AnthropicAgent()
result = agent.run("Generate FFN assembly for llama-3.2-1b with batch=4")
```

### Tools (TODO: implement stubs)

| Tool | Input | Output |
|------|-------|--------|
| `get_workload` | model_name, layer_type | hidden_size, weight shapes, hw_config |
| `get_template` | layer_name | Python template source |
| `get_assembly_code_examples` | mode (one-shot/few-shot) | .asm file contents |
| `get_doc` | topic (isa/registers/memory/config) | documentation |
| `machine_code_generation` | assembly_code | syntax_errors, instruction_count |
| `run_simulator` | assembly_code | latency, accuracy (mse/mae), errors |
| `get_instruction_size` | assembly_code | instruction count by opcode |

## Key Files for Reference

- `behavioral_simulator/testbench/ffn_test.py` - Full test example
- `compiler/asm_templates/ffn_asm.py` - FFN assembly template
- `tools/assembler/assembly_to_binary.py` - AssemblyToBinary class
- `behavioral_simulator/testbench/check_mem.py` - Accuracy comparison
