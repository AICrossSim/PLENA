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


def run_task(task: str, model: str = "claude-sonnet-4-20250514", max_iterations: int = 20):
    """Run a single task with the agent."""
    agent = AnthropicAgent(model=model)
    result = agent.run(task, max_iterations=max_iterations, verbose=True)
    return result


def interactive_mode(model: str = "claude-sonnet-4-20250514"):
    """Run in interactive chat mode."""
    agent = AnthropicAgent(model=model)
    print("PLENA Assembly Agent (interactive mode)")
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
    parser.add_argument("--max-iterations", "-n", type=int, default=5, help="Max iterations")
    args = parser.parse_args()

    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Run: export ANTHROPIC_API_KEY='your-key'")
        sys.exit(1)

    if args.interactive:
        interactive_mode(model=args.model)
    elif args.task:
        result = run_task(args.task, model=args.model, max_iterations=args.max_iterations)
        print("\n" + "=" * 60)
        print("FINAL RESULT:")
        print("=" * 60)
        print(result)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
