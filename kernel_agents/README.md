# Kernel Agents

Anthropic-based agents for assembly code generation and optimization.

## Setup

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

## Usage

```python
from kernel_agents.anthropic import AnthropicAgent

agent = AnthropicAgent(model="claude-sonnet-4-20250514")
result = agent.run("Generate FFN assembly for llama-3.1-8b")
print(result)
```

## Tools

Tools are in `anthropic/tools/` - implement the `NotImplementedError` stubs.
