# Model Library

PLENA includes pre-configured model specifications for various LLaMA and Qwen models.

## Available Models

| Model | File | Parameters | Description |
|-------|------|------------|-------------|
| LLaMA 3.2 1B | `llama-3.2-1b.json` | 1B | Compact model for testing |
| LLaMA 3 8B | `llama-3-8b.json` | 8B | Standard evaluation model |
| LLaMA 3.1 8B | `llama-3.1-8b.json` | 8B | Updated 8B variant |
| LLaMA 3.1 8B W8A8 | `llama-3.1-8b-w8a8.json` | 8B | 8-bit quantized variant |
| LLaMA 3.1 70B | `llama-3.1-70b.json` | 70B | Large model |
| LLaMA 3.3 70B | `llama-3.3-70b.json` | 70B | Latest 70B variant |
| LLaMA 3.1 405B | `estimated-llama-3.1-405b.json` | 405B | Largest model (estimated) |
| Qwen 2.5 7B | `qwen2_5_7b.json` | 7B | Qwen model family |

## Model Configuration Format

Each model JSON file contains:

```json
{
    "model_name": "Meta-Llama/Meta-Llama-3-8B",
    "num_hidden_layers": 32,
    "hidden_size": 4096,
    "intermediate_size": 14336,
    "num_attention_heads": 32,
    "num_key_value_heads": 8,
    "head_dim": 128,
    "vocab_size": 128256,
    "max_position_embeddings": 8192
}
```

### Key Parameters

| Parameter | Description |
|-----------|-------------|
| `num_hidden_layers` | Number of transformer layers |
| `hidden_size` | Model hidden dimension |
| `intermediate_size` | FFN intermediate dimension |
| `num_attention_heads` | Number of attention heads |
| `num_key_value_heads` | Number of KV heads (for GQA) |
| `head_dim` | Dimension per attention head |
| `vocab_size` | Vocabulary size |
| `max_position_embeddings` | Maximum sequence length |

## Using Models

### In Configuration

```toml
[MODEL]
name = "Meta-Llama/Meta-Llama-3-8B"
config_path = "doc/Model_Lib/llama-3-8b.json"
```

### Programmatically

```python
import json

with open("doc/Model_Lib/llama-3-8b.json") as f:
    model_config = json.load(f)

# Use in latency calculation
from co_design.interface import get_latency
latency = get_latency(hardware_config, model_config)
```

## Adding Custom Models

To add a new model:

1. Create a JSON file in `doc/Model_Lib/`
2. Include all required parameters
3. Reference in your configuration

```json
{
    "model_name": "your-org/your-model",
    "num_hidden_layers": 24,
    "hidden_size": 2048,
    "intermediate_size": 8192,
    "num_attention_heads": 16,
    "num_key_value_heads": 4,
    "head_dim": 128,
    "vocab_size": 32000,
    "max_position_embeddings": 4096
}
```

## Model Selection Guidelines

| Use Case | Recommended Model |
|----------|-------------------|
| Quick testing | LLaMA 3.2 1B |
| Standard evaluation | LLaMA 3 8B |
| Production optimization | LLaMA 3.1 70B |
| Extreme scale analysis | LLaMA 3.1 405B |
