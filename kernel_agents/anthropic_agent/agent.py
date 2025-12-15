"""
Anthropic agent for multi-turn iterative assembly generation.
"""
from __future__ import annotations

import json
from typing import Dict, List, Any, Optional

import anthropic as anthropic_sdk
from .system_prompt import get_system_prompt

from .tools import (
    machine_code_generation,
    run_simulator,
    get_instruction_size,
    get_workload,
    debug_view_memory,
    read_file,
)


# Tool definitions in Anthropic format
TOOLS = [
    {
        "name": "run_simulator",
        "description": """Run full simulation: assemble code, setup test data, execute, check accuracy.

This is the PRIMARY tool for testing assembly code. It does everything automatically:
1. Assembles your assembly code (checks syntax)
2. Creates random test inputs based on layer_type/dimensions
3. Computes golden output using PyTorch
4. Runs the behavioral simulator
5. Compares output to golden reference

Returns:
- success: bool - True if simulation completed
- latency_ns: float - Execution time in nanoseconds
- mse: float - Mean Squared Error vs golden. Must be close to target ~8.41e-04 (small margin allowed)
- errors: list - Any errors encountered

IMPORTANT: If model_name is provided, dimensions are auto-loaded from model config.
This ensures test dimensions match the model you're generating assembly for.

Success criteria: MSE close to ~8.41e-04. Keep iterating until this is achieved.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "assembly_code": {"type": "string", "description": "PLENA assembly code to test"},
                "layer_type": {
                    "type": "string",
                    "enum": ["linear", "ffn", "rms_norm", "silu"],
                    "description": "Layer type for test data generation (default: linear)",
                },
                "model_name": {
                    "type": "string",
                    "description": "Model name (e.g., 'llama-3.2-1b') - auto-loads hidden_size/intermediate_size from config",
                },
                "hidden_size": {"type": "integer", "description": "Input dimension (default: 128, overridden if model_name provided)"},
                "output_size": {"type": "integer", "description": "Output dimension for linear layer (default: same as hidden_size)"},
                "intermediate_size": {
                    "type": "integer",
                    "description": "FFN intermediate size (default: 4*hidden_size, only used for ffn)",
                },
                "batch_size": {"type": "integer", "description": "Batch size (default: 4)"},
                "seq_len": {"type": "integer", "description": "Sequence length (default: 1)"},
            },
            "required": ["assembly_code"],
        },
    },
    {
        "name": "get_workload",
        "description": """Get model dimensions and FP_SRAM layout for a specific layer type.

Use this to get correct dimensions (hidden_size, intermediate_size, etc.) for real models.
Returns:
- hw_config: Hardware config (MLEN=64, VLEN=64, BLEN=4)
- layer-specific shapes
- fp_sram_layout: CRITICAL - tells you which constants are at which FP_SRAM indices.
  ALWAYS check fp_sram_layout to know where 1.0, epsilon, etc. are stored.
  Example for silu: {0: "0.0", 1: "1.0"} means load 1.0 from index 1, not 0.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "model_name": {
                    "type": "string",
                    "description": "Model name (e.g., 'llama-3.2-1b', 'llama-3.1-8b')",
                },
                "layer_type": {
                    "type": "string",
                    "enum": ["ffn", "attention", "projection", "rms_norm", "silu"],
                    "description": "Layer type",
                },
                "batch_size": {"type": "integer", "description": "Batch size (default: 1)"},
                "seq_len": {"type": "integer", "description": "Sequence length (default: 1)"},
            },
            "required": ["model_name", "layer_type"],
        },
    },
    {
        "name": "machine_code_generation",
        "description": """Check assembly syntax by assembling to machine code.

Use this for quick syntax validation without running full simulation. you have to first generate the machine code to be runed in the simulator, you cannot run the assmbely code in the simulator
Returns syntax_errors list and instruction_count.""",
        "input_schema": {
            "type": "object",
            "properties": {"assembly_code": {"type": "string", "description": "PLENA assembly code"}},
            "required": ["assembly_code"],
        },
    },
    {
        "name": "get_instruction_size",
        "description": """Count and categorize instructions in assembly code.

Returns breakdown by category (Matrix, Vector, Scalar, HBM, Control).""",
        "input_schema": {
            "type": "object",
            "properties": {"assembly_code": {"type": "string", "description": "PLENA assembly code"}},
            "required": ["assembly_code"],
        },
    },
    {
        "name": "debug_view_memory",
        "description": """View simulator memory output and compare with golden reference for debugging.

Use this tool when MSE is high to understand what went wrong:
- See actual values produced by your assembly code
- Compare side-by-side with expected golden values
- Identify patterns: all zeros = not computed, wrong values = incorrect addressing

BEFORE calling this tool, you MUST trace your code in your thinking:
1. Pick a specific line (e.g., "Line 47: H_PREFETCH_M ...")
2. Trace each register value back to where it was set
3. Write out the calculation explicitly in your thinking
4. If wrong, fix that specific line - don't rewrite from scratch

IMPORTANT: Set num_batches and hidden_size to match your test configuration!
Default is batch=4, hidden=128. If debugging fails, try skip_reorder=True for raw memory view.

Returns per-row analysis showing simulated vs golden values, min/max/mean stats, and row-level MSE.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "assembly_code": {
                    "type": "string",
                    "description": "The assembly code being debugged (pass your current code)",
                },
                "num_rows": {
                    "type": "integer",
                    "description": "Number of rows to display (default 8, each row = 64 values)",
                },
                "start_row": {
                    "type": "integer",
                    "description": "Starting row index (default 0)",
                },
                "show_golden": {
                    "type": "boolean",
                    "description": "Whether to show golden reference values (default True)",
                },
                "num_batches": {
                    "type": "integer",
                    "description": "Number of batches in output - MUST match your test config (default 4)",
                },
                "hidden_size": {
                    "type": "integer",
                    "description": "Hidden dimension size - MUST match your test config (default 128)",
                },
                "skip_reorder": {
                    "type": "boolean",
                    "description": "Skip stride reordering for raw memory view (default False). Use if debug fails.",
                },
            },
            "required": ["assembly_code"],
        },
    },
    {
        "name": "read_file",
        "description": """Read a file from the codebase for deeper understanding.

Use sparingly - only when documentation is insufficient. Prefer existing tools first.

DO NOT read from compiler/asm_templates/ - you must write assembly from first principles
using the ISA spec and memory layout docs provided in the system prompt.

Useful paths:
- behavioral_simulator/src/op.rs - Instruction execution logic
- behavioral_simulator/testbench/check_mem.py - Golden comparison, MSE calculation
- tools/assembler/assembly_to_binary.py - Assembler implementation
- src/definitions/configuration.svh - Hardware params (VLEN, MLEN, BLEN)""",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative path from project root (e.g., 'behavioral_simulator/src/op.rs')",
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum lines to return (default 500)",
                },
            },
            "required": ["file_path"],
        },
    },
]

# Tool function registry
TOOL_FUNCTIONS = {
    "machine_code_generation": machine_code_generation,
    "run_simulator": run_simulator,
    "get_instruction_size": get_instruction_size,
    "get_workload": get_workload,
    "debug_view_memory": debug_view_memory,
    "read_file": read_file,
}



class AnthropicAgent:
    """
    Multi-turn iterative agent using Anthropic Claude API.

    Supports:
    - Tool calling with automatic execution
    - Multi-turn conversation with message history
    - Iterative refinement based on errors
    - Extended thinking for complex reasoning
    """

    def __init__(
        self,
        model: str = "claude-opus-4-20250514",
        api_key: Optional[str] = None,
        max_tokens: int = 16000,
        system_prompt: Optional[str] = None,
        enable_thinking: bool = True,
        thinking_budget: int = 10000,
        include_examples: bool = False,
    ):
        """
        Initialize the agent.

        Args:
            model: Claude model to use
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            max_tokens: Max tokens per response
            system_prompt: Custom system prompt (defaults to SYSTEM_PROMPT)
            enable_thinking: Enable extended thinking for better reasoning
            thinking_budget: Token budget for thinking (default 10000)
            include_examples: Include working assembly examples in system prompt (default False)
        """
        self.client = anthropic_sdk.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt or get_system_prompt(include_examples=include_examples)
        self.messages: List[Dict] = []
        self.tools = list(TOOLS)  # Copy to allow modifications
        self.tool_functions = dict(TOOL_FUNCTIONS)
        self.enable_thinking = enable_thinking
        self.thinking_budget = thinking_budget

    def reset(self):
        """Clear conversation history."""
        self.messages = []

    def add_tool(self, name: str, func: Any, schema: Dict):
        """
        Register a custom tool.

        Args:
            name: Tool name
            func: Tool function
            schema: Anthropic tool schema
        """
        self.tool_functions[name] = func
        self.tools.append(schema)

    def execute_tool(self, name: str, inputs: Dict) -> Any:
        """
        Execute a tool by name.

        Args:
            name: Tool name
            inputs: Tool input arguments

        Returns:
            Tool result (dict or string)
        """
        if name not in self.tool_functions:
            return {"error": f"Unknown tool: {name}"}
        try:
            return self.tool_functions[name](**inputs)
        except NotImplementedError as e:
            return {"error": f"Tool not implemented: {e}"}
        except Exception as e:
            return {"error": str(e)}

    def step(self, user_message: Optional[str] = None) -> Dict:
        """
        Run one step of the agent loop.

        Args:
            user_message: Optional user message to add

        Returns:
            Dict with 'done' bool, 'response' text, 'tool_calls' list
        """
        if user_message:
            self.messages.append({"role": "user", "content": user_message})

        # Call Claude with optional extended thinking
        api_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": self.system_prompt,
            "tools": self.tools,
            "messages": self.messages,
        }

        if self.enable_thinking:
            api_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": self.thinking_budget,
            }

        response = self.client.messages.create(**api_params)
        # breakpoint()


        # Check if done
        if response.stop_reason == "end_turn":
            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text = block.text
                    break
            return {"done": True, "response": text, "tool_calls": []}

        # Process tool calls
        if response.stop_reason == "tool_use":
            self.messages.append({"role": "assistant", "content": response.content})

            tool_calls = []
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    tool_calls.append({"name": block.name, "input": block.input})
                    result = self.execute_tool(block.name, block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result) if not isinstance(result, str) else result,
                        }
                    )

            self.messages.append({"role": "user", "content": tool_results})
            return {"done": False, "response": "", "tool_calls": tool_calls}

        return {"done": True, "response": "", "tool_calls": []}

    def run(self, task: str, max_iterations: int = 20, verbose: bool = True) -> str:
        """
        Run the agent on a task until completion.

        Args:
            task: Task description
            max_iterations: Maximum tool call iterations
            verbose: Print progress

        Returns:
            Final response text
        """
        self.reset()

        if verbose:
            print("=" * 70)
            print(f"[TASK] {task}")
            print("=" * 70)

        result = self.step(task)
        iteration = 0

        for i in range(max_iterations):
            iteration = i + 1
            if result["done"]:
                if verbose:
                    print("-" * 70)
                    print(f"[COMPLETED] Finished in {iteration} iterations")
                    print("-" * 70)
                return result["response"]

            if verbose and result["tool_calls"]:
                print(f"\n{'='*70}")
                print(f"[ITERATION {iteration}]")
                print("=" * 70)

                # Debug: show content block types
                for msg in reversed(self.messages):
                    if msg.get("role") == "assistant":
                        content = msg.get("content", [])
                        if isinstance(content, list):
                            block_types = [getattr(b, "type", "unknown") for b in content]
                            print(f"[DEBUG] Response block types: {block_types}")
                        break

                # Print agent's reasoning/thinking if present
                thinking = self._extract_thinking_from_last_response()
                if thinking:
                    print(f"\n[AGENT THINKING]")
                    print(f"{thinking[:1000]}{'...' if len(thinking) > 1000 else ''}")

                # Print each tool call with input and output
                for tc in result["tool_calls"]:
                    print(f"\n[TOOL CALL] {tc['name']}")
                    print(f"  Input: {self._format_tool_input(tc['input'])}")

                # Execute and get results
                tool_results = self._get_last_tool_results()
                if tool_results:
                    for tr in tool_results:
                        print(f"\n[TOOL RESULT] {tr.get('name', 'unknown')}")
                        self._print_tool_result(tr.get("result", tr.get("content", "")))

            result = self.step()

        if verbose:
            print(f"\n[WARNING] Max iterations ({max_iterations}) reached")
        return "Max iterations reached"

    def _extract_thinking_from_last_response(self) -> str:
        """Extract thinking/text from the last assistant message."""
        if not self.messages:
            return ""
        for msg in reversed(self.messages):
            if msg.get("role") == "assistant":
                content = msg.get("content", [])
                if isinstance(content, list):
                    # First try to get thinking block (extended thinking)
                    for block in content:
                        block_type = getattr(block, "type", None)
                        if block_type == "thinking":
                            # Thinking content is in .thinking attribute
                            thinking_text = getattr(block, "thinking", None)
                            if thinking_text:
                                return thinking_text
                    # Fallback to text block
                    for block in content:
                        if hasattr(block, "text") and block.text:
                            return block.text
                elif isinstance(content, str):
                    return content
        return ""

    def _get_last_tool_results(self) -> list:
        """Get tool results from the last user message (tool results)."""
        if not self.messages:
            return []
        last_msg = self.messages[-1]
        if last_msg.get("role") == "user":
            content = last_msg.get("content", [])
            if isinstance(content, list):
                results = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        results.append(item)
                return results
        return []

    def _format_tool_input(self, input_dict: Dict) -> str:
        """Format tool input for display, truncating large values."""
        if not input_dict:
            return "{}"
        formatted = {}
        for k, v in input_dict.items():
            if isinstance(v, str) and len(v) > 100:
                # Truncate long strings (like assembly code)
                formatted[k] = f"{v[:100]}... ({len(v)} chars)"
            else:
                formatted[k] = v
        return json.dumps(formatted, indent=2)

    def _print_tool_result(self, result: Any):
        """Print tool result with special formatting for simulator results."""
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except (json.JSONDecodeError, TypeError):
                print(f"  {result[:300]}{'...' if len(str(result)) > 300 else ''}")
                return

        if isinstance(result, dict):
            # Special formatting for run_simulator results
            if "latency_ns" in result or "mse" in result:
                print(f"  {'─'*40}")
                print(f"  success:     {result.get('success', 'N/A')}")
                print(f"  latency_ns:  {result.get('latency_ns', 'N/A')}")
                print(f"  mse:         {result.get('mse', 'N/A')}")
                print(f"  match_rate:  {result.get('match_rate', 'N/A')}")
                print(f"  instr_count: {result.get('instruction_count', 'N/A')}")
                if result.get("errors"):
                    print(f"  errors:      {result.get('errors')}")
                if result.get("test_config"):
                    print(f"  test_config: {result.get('test_config')}")
                print(f"  {'─'*40}")
            # Generic dict formatting
            else:
                result_str = json.dumps(result, indent=2, default=str)
                if len(result_str) > 500:
                    print(f"  {result_str[:500]}...")
                else:
                    print(f"  {result_str}")
        else:
            print(f"  {str(result)[:300]}")

    def chat(self, message: str) -> str:
        """
        Send a single message and get response (maintains history).

        Args:
            message: User message

        Returns:
            Assistant response
        """
        result = self.step(message)

        while not result["done"]:
            result = self.step()

        return result["response"]


def main():
    """Example usage."""
    agent = AnthropicAgent(model="claude-sonnet-4-20250514")

    # Single task run
    result = agent.run(
        "Generate optimized assembly code for a simple linear layer with hidden_size=128, batch=4. "
        "First get the workload info, then write assembly and test it."
    )
    print("\n" + "=" * 60)
    print("RESULT:")
    print("=" * 60)
    print(result)


if __name__ == "__main__":
    main()
