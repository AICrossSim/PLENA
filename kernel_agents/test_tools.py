#!/usr/bin/env python3
"""
Test each agent tool separately.

Usage:
    python kernel_agents/test_tools.py
    python kernel_agents/test_tools.py --tool setup_test_environment
    python kernel_agents/test_tools.py --tool run_simulator
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
    get_assembly_code_examples,
    machine_code_generation,
    run_simulator,
    setup_test_environment,
    get_instruction_size,
    get_template,
    get_doc,
    get_workload,
)


def test_get_doc():
    """Test ISA documentation retrieval."""
    print("\n" + "="*60)
    print("TEST: get_doc('isa')")
    print("="*60)
    result = get_doc("isa")
    print(result[:1000] + "..." if len(result) > 1000 else result)


def test_get_workload():
    """Test workload dimensions retrieval."""
    print("\n" + "="*60)
    print("TEST: get_workload('llama-3.2-1b', 'ffn')")
    print("="*60)
    result = get_workload("llama-3.2-1b", "ffn", batch_size=4)
    for k, v in result.items():
        print(f"  {k}: {v}")


def test_get_template():
    """Test template retrieval."""
    print("\n" + "="*60)
    print("TEST: get_template('projection')")
    print("="*60)
    result = get_template("projection")
    print(result[:1500] + "..." if len(result) > 1500 else result)


def test_get_examples():
    """Test assembly examples retrieval."""
    print("\n" + "="*60)
    print("TEST: get_assembly_code_examples('one-shot')")
    print("="*60)
    result = get_assembly_code_examples(mode="one-shot")
    print(result[:1500] + "..." if len(result) > 1500 else result)


def test_setup_environment():
    """Test environment setup (creates HBM files)."""
    print("\n" + "="*60)
    print("TEST: setup_test_environment()")
    print("="*60)
    result = setup_test_environment(
        layer_type="linear",
        hidden_size=128,
        batch_size=4
    )
    print(f"  success: {result['success']}")
    print(f"  message: {result['message']}")
    print(f"  golden_output_shape: {result['golden_output_shape']}")
    if result['assembly_code']:
        lines = result['assembly_code'].split('\n')
        print(f"  assembly_code: {len(lines)} lines")
    return result


def test_machine_code(assembly_code: str):
    """Test machine code generation (syntax check)."""
    print("\n" + "="*60)
    print("TEST: machine_code_generation()")
    print("="*60)
    result = machine_code_generation(assembly_code)
    print(f"  success: {result['success']}")
    print(f"  instruction_count: {result['instruction_count']}")
    if result['syntax_errors']:
        print(f"  syntax_errors: {result['syntax_errors']}")
    return result


def test_instruction_size(assembly_code: str):
    """Test instruction counting."""
    print("\n" + "="*60)
    print("TEST: get_instruction_size()")
    print("="*60)
    result = get_instruction_size(assembly_code)
    print(f"  total: {result['total']}")
    print(f"  by_type: {result['by_type']}")


def test_run_simulator(assembly_code: str):
    """Test full simulator run."""
    print("\n" + "="*60)
    print("TEST: run_simulator()")
    print("="*60)
    result = run_simulator(assembly_code)
    print(f"  success: {result['success']}")
    print(f"  instruction_count: {result['instruction_count']}")
    print(f"  latency_cycles: {result['latency_cycles']}")
    print(f"  latency_ns: {result['latency_ns']}")
    print(f"  accuracy: {result['accuracy']}")
    if result['errors']:
        print(f"  errors: {result['errors']}")
    return result


def run_all_tests():
    """Run all tool tests in sequence."""
    # 1. Documentation tools
    test_get_doc()
    test_get_workload()
    test_get_template()
    test_get_examples()

    # 2. Setup environment (creates HBM files)
    env_result = test_setup_environment()

    if env_result['success'] and env_result['assembly_code']:
        asm = env_result['assembly_code']

        # 3. Test assembly tools
        test_machine_code(asm)
        test_instruction_size(asm)

        # 4. Run simulator
        test_run_simulator(asm)
    else:
        print("\nSkipping simulator tests - environment setup failed")


def run_single_tool(tool_name: str):
    """Run a single tool test."""
    if tool_name == "get_doc":
        test_get_doc()
    elif tool_name == "get_workload":
        test_get_workload()
    elif tool_name == "get_template":
        test_get_template()
    elif tool_name == "get_examples":
        test_get_examples()
    elif tool_name == "setup_test_environment":
        test_setup_environment()
    elif tool_name == "machine_code_generation":
        # Need assembly code first
        env = test_setup_environment()
        if env['success']:
            test_machine_code(env['assembly_code'])
    elif tool_name == "get_instruction_size":
        env = test_setup_environment()
        if env['success']:
            test_instruction_size(env['assembly_code'])
    elif tool_name == "run_simulator":
        env = test_setup_environment()
        if env['success']:
            test_run_simulator(env['assembly_code'])
    else:
        print(f"Unknown tool: {tool_name}")
        print("Available tools: get_doc, get_workload, get_template, get_examples,")
        print("                 setup_test_environment, machine_code_generation,")
        print("                 get_instruction_size, run_simulator")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test agent tools separately")
    parser.add_argument("--tool", "-t", help="Specific tool to test (default: run all)")
    args = parser.parse_args()

    if args.tool:
        run_single_tool(args.tool)
    else:
        run_all_tests()
