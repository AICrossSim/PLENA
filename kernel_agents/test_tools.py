#!/usr/bin/env python3
"""
Test each agent tool separately.

Usage:
    python kernel_agents/test_tools.py
    python kernel_agents/test_tools.py --tool run_simulator
    python kernel_agents/test_tools.py --tool get_workload
"""

import sys
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))
sys.path.insert(0, str(PROJECT_ROOT / "compiler"))
sys.path.insert(0, str(PROJECT_ROOT / "behavioral_simulator" / "testbench"))

from kernel_agents.anthropic_agent.tools import (
    machine_code_generation,
    run_simulator,
    get_instruction_size,
    get_doc,
    get_workload,
)


# Sample assembly code for testing
SAMPLE_LINEAR_ASM = """; Linear Test with Loop Instructions
; Preload Addr Reg Generation
S_ADDI_INT gp1, gp0, 576
C_SET_ADDR_REG a1, gp0, gp1
S_ADDI_INT gp2, gp0, 19152
C_SET_ADDR_REG a2, gp0, gp2
; Reset Registers [[1, 2, 3]]
S_ADDI_INT gp1, gp0, 0
S_ADDI_INT gp2, gp0, 0
S_ADDI_INT gp3, gp0, 0
; Preload Activation Generation
S_ADDI_INT gp1, gp0, 512
C_SET_SCALE_REG gp1
S_ADDI_INT gp1, gp0, 0
S_ADDI_INT gp3, gp0, 0
S_ADDI_INT gp2, gp0, 128
C_SET_STRIDE_REG gp2
C_LOOP_START gp4, 2
S_ADDI_INT gp2, gp1, 0
H_PREFETCH_V gp3, gp2, a0, 1, 0
S_ADDI_INT gp3, gp3, 256
S_ADDI_INT gp1, gp1, 64
C_LOOP_END gp4
; Reset Registers [[1, 2, 3, 4, 5, 6, 7]]
S_ADDI_INT gp1, gp0, 0
S_ADDI_INT gp2, gp0, 0
S_ADDI_INT gp3, gp0, 0
S_ADDI_INT gp4, gp0, 0
S_ADDI_INT gp5, gp0, 0
S_ADDI_INT gp6, gp0, 0
S_ADDI_INT gp7, gp0, 0
; Projection Generation (Loop-Optimized)
S_ADDI_INT gp4, gp0, 16384
C_SET_SCALE_REG gp4
S_ADDI_INT gp4, gp0, 128
C_SET_STRIDE_REG gp4
S_ADDI_INT gp4, gp0, 0
S_ADDI_INT gp1, gp0, 512
S_ADDI_INT gp3, gp0, 0
; Outer loop: 2 MLEN blocks
C_LOOP_START gp5, 2
S_ADDI_INT gp2, gp0, 0
H_PREFETCH_M gp2, gp3, a1, 1, 0
S_ADDI_INT gp3, gp3, 8192
S_ADDI_INT gp2, gp2, 4096
H_PREFETCH_M gp2, gp3, a1, 1, 0
S_ADDI_INT gp7, gp0, 0
; Middle loop: 16 iterations (unroll=1)
C_LOOP_START gp6, 16
M_MM 0, gp7, gp4
S_ADDI_INT gp2, gp7, 4096
S_ADDI_INT gp4, gp4, 256
M_MM 0, gp2, gp4
M_MM_WO 1, gp0, 0
S_ADDI_INT gp1, gp1, 4
S_ADDI_INT gp7, gp7, 4
S_ADDI_INT gp4, gp0, 0
C_LOOP_END gp6
S_ADDI_INT gp1, gp1, 192
S_ADDI_INT gp7, gp0, 8128
S_SUB_INT gp3, gp3, gp7
C_LOOP_END gp5
"""


def test_get_doc():
    """Test ISA documentation retrieval."""
    print("\n" + "=" * 60)
    print("TEST: get_doc() - Summary")
    print("=" * 60)
    result = get_doc()
    print(f"  Available topics: {list(result.get('available_topics', {}).keys())}")
    print(f"  Quick ref keys: {list(result.get('quick_reference', {}).keys())}")

    print("\n" + "=" * 60)
    print("TEST: get_doc('isa') - Full ISA spec")
    print("=" * 60)
    result_isa = get_doc("isa")
    content = result_isa.get("content", "")
    print(f"  Format: {result_isa.get('format', 'N/A')}")
    print(f"  File: {result_isa.get('file_path', 'N/A')}")
    print(f"  Content length: {len(content)} chars")
    print(f"  Preview: {content[:200]}...")

    print("\n" + "=" * 60)
    print("TEST: get_doc('memory') - Memory layout")
    print("=" * 60)
    result_mem = get_doc("memory")
    print(f"  Memory types: {list(result_mem.get('memory_types', {}).keys())}")

    return result


def test_get_workload():
    """Test workload dimensions retrieval."""
    print("\n" + "=" * 60)
    print("TEST: get_workload('llama-3.2-1b', 'ffn')")
    print("=" * 60)
    result = get_workload("llama-3.2-1b", "ffn", batch_size=4)
    for k, v in result.items():
        print(f"  {k}: {v}")
    return result


def test_machine_code():
    """Test machine code generation (syntax check)."""
    print("\n" + "=" * 60)
    print("TEST: machine_code_generation()")
    print("=" * 60)
    result = machine_code_generation(SAMPLE_LINEAR_ASM)
    print(f"  success: {result['success']}")
    print(f"  instruction_count: {result['instruction_count']}")
    if result["syntax_errors"]:
        print(f"  syntax_errors: {result['syntax_errors']}")
    return result


def test_instruction_size():
    """Test instruction counting."""
    print("\n" + "=" * 60)
    print("TEST: get_instruction_size()")
    print("=" * 60)
    result = get_instruction_size(SAMPLE_LINEAR_ASM)
    print(f"  total_instructions: {result.get('total_instructions', 0)}")
    print(f"  by_category: {result.get('by_category', {})}")
    return result


def test_run_simulator():
    """Test full simulator run with integrated setup."""
    print("\n" + "=" * 60)
    print("TEST: run_simulator() - Full pipeline test")
    print("=" * 60)
    result = run_simulator(
        assembly_code=SAMPLE_LINEAR_ASM,
        layer_type="linear",
        hidden_size=128,
        batch_size=4,
        seq_len=1,
    )
    print(f"  success:     {result['success']}")
    print(f"  latency_ns:  {result['latency_ns']}")
    print(f"  mse:         {result['mse']}")
    print(f"  match_rate:  {result['match_rate']}")
    print(f"  instr_count: {result['instruction_count']}")
    print(f"  test_config: {result['test_config']}")
    if result["errors"]:
        print(f"  errors:      {result['errors']}")
    return result


def run_all_tests():
    """Run all tool tests in sequence."""
    print("=" * 60)
    print("RUNNING ALL TOOL TESTS")
    print("=" * 60)

    # 1. Documentation tools
    test_get_doc()
    test_get_workload()

    # 2. Assembly analysis tools
    test_machine_code()
    test_instruction_size()

    # 3. Full simulation (includes setup)
    test_run_simulator()

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)


def run_single_tool(tool_name: str):
    """Run a single tool test."""
    tool_tests = {
        "get_doc": test_get_doc,
        "get_workload": test_get_workload,
        "machine_code_generation": test_machine_code,
        "get_instruction_size": test_instruction_size,
        "run_simulator": test_run_simulator,
    }

    if tool_name in tool_tests:
        tool_tests[tool_name]()
    else:
        print(f"Unknown tool: {tool_name}")
        print(f"Available tools: {', '.join(tool_tests.keys())}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test agent tools separately")
    parser.add_argument("--tool", "-t", help="Specific tool to test (default: run all)")
    args = parser.parse_args()

    if args.tool:
        run_single_tool(args.tool)
    else:
        run_all_tests()
