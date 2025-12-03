"""
Anthropic agent for multi-turn iterative assembly generation.
"""

import os
import json
from typing import Dict, List, Any, Optional

import anthropic

from .tools import (
    get_assembly_code_examples,
    machine_code_generation,
    run_simulator,
    get_instruction_size,
    get_template,
    get_doc,
    get_workload,
)


# Tool definitions in Anthropic format
TOOLS = [
    {
        "name": "get_assembly_code_examples",
        "description": "Get assembly code examples for reference",
        "input_schema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["one-shot", "few-shot"],
                    "description": "one-shot for single example, few-shot for multiple"
                },
                "layer_type": {
                    "type": "string",
                    "description": "Optional filter (e.g., 'projection', 'rms', 'attention')"
                }
            },
            "required": []
        }
    },
    {
        "name": "machine_code_generation",
        "description": "Check assembly syntax by generating machine code. Returns syntax errors (if any) and instruction count. Does NOT return binary data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "assembly_code": {
                    "type": "string",
                    "description": "PLENA assembly code"
                }
            },
            "required": ["assembly_code"]
        }
    },
    {
        "name": "run_simulator",
        "description": "Run full simulation pipeline: assembles code, runs simulator, checks accuracy. Returns latency, accuracy metrics, and any errors. Use this as the main test tool.",
        "input_schema": {
            "type": "object",
            "properties": {
                "assembly_code": {
                    "type": "string",
                    "description": "PLENA assembly code"
                }
            },
            "required": ["assembly_code"]
        }
    },
    {
        "name": "get_instruction_size",
        "description": "Count instructions in assembly code",
        "input_schema": {
            "type": "object",
            "properties": {
                "assembly_code": {
                    "type": "string",
                    "description": "PLENA assembly code"
                }
            },
            "required": ["assembly_code"]
        }
    },
    {
        "name": "get_template",
        "description": "Get Python assembly template for a layer type",
        "input_schema": {
            "type": "object",
            "properties": {
                "layer_name": {
                    "type": "string",
                    "enum": ["ffn", "attention", "projection", "rms_norm", "embedding", "elementwise_add"],
                    "description": "Layer type"
                }
            },
            "required": ["layer_name"]
        }
    },
    {
        "name": "get_doc",
        "description": "Get ISA or hardware documentation",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "enum": ["isa", "registers", "memory", "config"],
                    "description": "Documentation topic"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_workload",
        "description": "Get model dimensions for a specific workload (e.g., FFN for llama-3.2-1b). Returns hidden_size, intermediate_size, weight shapes, and hardware config.",
        "input_schema": {
            "type": "object",
            "properties": {
                "model_name": {
                    "type": "string",
                    "description": "Model name (e.g., 'llama-3.2-1b', 'llama-3.1-8b')"
                },
                "layer_type": {
                    "type": "string",
                    "enum": ["ffn", "attention", "projection", "rms_norm"],
                    "description": "Layer type"
                },
                "batch_size": {
                    "type": "integer",
                    "description": "Batch size (default 1)"
                },
                "seq_len": {
                    "type": "integer",
                    "description": "Sequence length (default 1)"
                }
            },
            "required": ["model_name", "layer_type"]
        }
    },
]

# Tool function registry
TOOL_FUNCTIONS = {
    "get_assembly_code_examples": get_assembly_code_examples,
    "machine_code_generation": machine_code_generation,
    "run_simulator": run_simulator,
    "get_instruction_size": get_instruction_size,
    "get_template": get_template,
    "get_doc": get_doc,
    "get_workload": get_workload,
}


SYSTEM_PROMPT = """You are an assembly code generator for the PLENA LLM accelerator.

Your goal is to generate optimized assembly code for neural network layers.

## Workflow
1. Call get_workload() to get model dimensions (hidden_size, intermediate_size, etc.)
2. Call get_template() to see the Python assembly template
3. Call get_assembly_code_examples() for reference code
4. Generate assembly code using the dimensions and patterns
5. Call machine_code_generation() to check for syntax errors
6. If errors, fix and retry
7. Call run_simulator() to execute and check accuracy
8. Iterate until accuracy is acceptable

## Key Registers
- gp0-gp15: Integer registers (gp0 = 0)
- f0-f7: Floating-point registers
- a0-a7: HBM address registers

## Common Instructions
- S_ADDI_INT gp1, gp0, 100  ; gp1 = 100
- M_MM 0, gp1, gp2          ; Matrix multiply
- V_ADD_VV gp3, gp1, gp2, 0 ; Vector add
- H_PREFETCH_M gp1, gp2, a0, 1, 0 ; Load from HBM

Always iterate until the code assembles correctly and passes accuracy checks.
"""


class AnthropicAgent:
    """
    Multi-turn iterative agent using Anthropic Claude API.

    Supports:
    - Tool calling with automatic execution
    - Multi-turn conversation with message history
    - Iterative refinement based on errors
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: Optional[str] = None,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
    ):
        """
        Initialize the agent.

        Args:
            model: Claude model to use
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            max_tokens: Max tokens per response
            system_prompt: Custom system prompt (defaults to SYSTEM_PROMPT)
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt or SYSTEM_PROMPT
        self.messages: List[Dict] = []
        self.tools = list(TOOLS)  # Copy to allow modifications
        self.tool_functions = dict(TOOL_FUNCTIONS)

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

        # Call Claude
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            tools=self.tools,
            messages=self.messages,
        )

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
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result) if not isinstance(result, str) else result
                    })

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
            print(f"[Agent] Starting task: {task[:80]}...")

        result = self.step(task)

        for i in range(max_iterations):
            if result["done"]:
                if verbose:
                    print(f"[Agent] Completed in {i + 1} iterations")
                return result["response"]

            if verbose and result["tool_calls"]:
                for tc in result["tool_calls"]:
                    print(f"  [Tool] {tc['name']}({str(tc['input'])[:50]}...)")

            result = self.step()

        if verbose:
            print(f"[Agent] Max iterations ({max_iterations}) reached")
        return "Max iterations reached"

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
        "Generate FFN assembly code for a small test. "
        "First get the template for FFN, then generate assembly code."
    )
    print("\n" + "=" * 60)
    print("RESULT:")
    print("=" * 60)
    print(result)


if __name__ == "__main__":
    main()
