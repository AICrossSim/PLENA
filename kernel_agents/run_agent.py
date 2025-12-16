#!/usr/bin/env python3
"""
Run the PLENA assembly generation agent.

Usage:
    python kernel_agents/run_agent.py "Generate FFN assembly for llama-3.2-1b"
    python kernel_agents/run_agent.py --interactive

Environment:
    ANTHROPIC_API_KEY: Your Anthropic API key
"""

import sys
import os
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))
sys.path.insert(0, str(PROJECT_ROOT / "compiler"))

from kernel_agents.anthropic_agent import AnthropicAgent


def build_task_prompt(
    task: str,
    layer_type: str,
    hidden_size: int,
    batch_size: int,
    seq_len: int,
    intermediate_size: int = None,
    output_size: int = None,
    num_heads: int = None,
) -> str:
    """Build task prompt with workload configuration."""
    import math
    # Set defaults based on layer type
    if intermediate_size is None:
        intermediate_size = hidden_size * 4
    if output_size is None:
        output_size = hidden_size
    if num_heads is None:
        num_heads = 1

    config_lines = [
        f"Layer type: {layer_type}",
        f"Batch size: {batch_size}",
        f"Sequence length: {seq_len}",
        f"Hidden size: {hidden_size}",
    ]

    if layer_type == "ffn":
        config_lines.append(f"Intermediate size: {intermediate_size}")
    elif layer_type == "linear":
        config_lines.append(f"Output size: {output_size}")
    elif layer_type == "attention":
        head_dim = hidden_size // num_heads
        qk_scale = 1.0 / math.sqrt(head_dim)
        config_lines.append(f"Number of heads: {num_heads}")
        config_lines.append(f"Head dimension: {head_dim}")
        config_lines.append(f"QK scale: {qk_scale:.6f}")

    config_str = "\n".join(config_lines)

    # Set FP_SRAM based on layer type
    if layer_type == "attention":
        head_dim = hidden_size // num_heads
        qk_scale = 1.0 / math.sqrt(head_dim)
        fp_sram_info = f"FP_SRAM[0]=0.0, FP_SRAM[1]={qk_scale:.6f} (qk_scale), FP_SRAM[2]=-inf (causal mask)"
    else:
        fp_sram_info = "FP_SRAM[0]=0.0, FP_SRAM[1]=1.0 (preloaded constants)"

    return f"""{task}

Workload Configuration:
{config_str}

Hardware: MLEN=64, VLEN=64, BLEN=4
{fp_sram_info}
"""


def run_task(
    task: str,
    model: str = "claude-sonnet-4-20250514",
    max_iterations: int = 20,
    layer_type: str = "linear",
    hidden_size: int = 128,
    batch_size: int = 4,
    seq_len: int = 1,
    intermediate_size: int = None,
    output_size: int = None,
    num_heads: int = None,
):
    """Run a single task with the agent."""
    agent = AnthropicAgent(model=model, layer_type=layer_type)
    full_task = build_task_prompt(
        task, layer_type, hidden_size, batch_size, seq_len, intermediate_size, output_size, num_heads
    )
    result = agent.run(full_task, max_iterations=max_iterations, verbose=True)
    return result


def interactive_mode(
    model: str = "claude-sonnet-4-20250514",
    layer_type: str = "linear",
    hidden_size: int = 128,
    batch_size: int = 4,
):
    """Run in interactive chat mode."""
    agent = AnthropicAgent(model=model, layer_type=layer_type)
    print(f"PLENA Assembly Agent (interactive mode)")
    print(f"Layer: {layer_type}, Hidden: {hidden_size}, Batch: {batch_size}")
    print("Type 'quit' to exit, 'reset' to clear history")
    print("-" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

        if not user_input:
            continue
        if user_input.lower() == 'quit':
            break
        if user_input.lower() == 'reset':
            agent.reset()
            print("[History cleared]")
            continue

        response = agent.chat(user_input)
        print(f"\nAgent: {response}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run PLENA assembly generation agent")
    parser.add_argument("task", nargs="?", help="Task to run (or use --interactive)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive chat mode")
    parser.add_argument("--model", "-m", default="claude-sonnet-4-20250514", help="Model to use")
    parser.add_argument("--max-iterations", "-n", type=int, default=20, help="Max iterations")
    parser.add_argument("--layer-type", "-l", default="linear",
                       choices=["linear", "ffn", "attention", "rms_norm", "silu", "softmax"],
                       help="Layer type (default: linear)")
    parser.add_argument("--hidden-size", "-H", type=int, default=128, help="Hidden size (default: 128)")
    parser.add_argument("--batch-size", "-b", type=int, default=4, help="Batch size (default: 4)")
    parser.add_argument("--seq-len", "-s", type=int, default=1, help="Sequence length (default: 1)")
    parser.add_argument("--intermediate-size", "-I", type=int, default=None,
                       help="FFN intermediate size (default: 4*hidden_size)")
    parser.add_argument("--output-size", "-o", type=int, default=None,
                       help="Linear output size (default: hidden_size)")
    parser.add_argument("--num-heads", "-N", type=int, default=None,
                       help="Number of attention heads (default: 1)")
    args = parser.parse_args()

    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Run: export ANTHROPIC_API_KEY='your-key'")
        sys.exit(1)

    if args.interactive:
        interactive_mode(
            model=args.model,
            layer_type=args.layer_type,
            hidden_size=args.hidden_size,
            batch_size=args.batch_size,
        )
    elif args.task:
        result = run_task(
            args.task,
            model=args.model,
            max_iterations=args.max_iterations,
            layer_type=args.layer_type,
            hidden_size=args.hidden_size,
            batch_size=args.batch_size,
            seq_len=args.seq_len,
            intermediate_size=args.intermediate_size,
            output_size=args.output_size,
            num_heads=args.num_heads,
        )
        print("\n" + "=" * 60)
        print("FINAL RESULT:")
        print("=" * 60)
        print(result)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
