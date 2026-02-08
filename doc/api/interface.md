# Interface Module

The interface module (`co_design/interface/`) provides the abstraction layer between the optimization engine and hardware/simulator backends.

## Module Overview

```
co_design/interface/
├── interface.py    # Core hardware metric functions
├── utils.py        # Configuration parsing utilities
└── __init__.py
```

## Core Functions

### `get_area()`

Calculates hardware resource utilization using the utilisation model.

```python
def get_area(config: dict) -> float:
    """
    Calculate area/resource utilization for a hardware configuration.

    Args:
        config: Hardware configuration dictionary

    Returns:
        Area metric (normalized utilization)
    """
```

**Usage:**
```python
from co_design.interface import get_area

area = get_area(hardware_config)
```

---

### `get_latency()`

Computes overall latency for LLM inference.

```python
def get_latency(config: dict, model_config: dict) -> float:
    """
    Calculate inference latency for given hardware and model configuration.

    Args:
        config: Hardware configuration dictionary
        model_config: Model specification (layers, dimensions, etc.)

    Returns:
        Latency in milliseconds
    """
```

**Usage:**
```python
from co_design.interface import get_latency

latency = get_latency(hardware_config, model_config)
```

---

### `get_accuracy()`

Runs accuracy evaluation via the simulator.

```python
def get_accuracy(config: dict, model_name: str) -> float:
    """
    Evaluate model accuracy with given precision configuration.

    Args:
        config: Precision configuration dictionary
        model_name: HuggingFace model identifier

    Returns:
        Accuracy score (0.0 to 1.0)
    """
```

**Usage:**
```python
from co_design.interface import get_accuracy

accuracy = get_accuracy(precision_config, "Meta-Llama/Meta-Llama-3-8B")
```

## Utility Functions

### `parse_precision_config()`

Extracts precision settings from a TOML configuration.

```python
def parse_precision_config(toml_path: str) -> dict:
    """
    Parse precision configuration from TOML file.

    Args:
        toml_path: Path to configuration file

    Returns:
        Dictionary with precision settings
    """
```

---

### `get_bit_width()`

Converts format strings to bit widths.

```python
def get_bit_width(format_str: str) -> int:
    """
    Convert precision format string to bit width.

    Args:
        format_str: Format string (e.g., "MXFP8", "MXINT4", "FP16")

    Returns:
        Bit width as integer

    Examples:
        get_bit_width("MXFP8")  -> 8
        get_bit_width("MXINT4") -> 4
        get_bit_width("FP16")   -> 16
    """
```

---

### `write_active_config_to_toml()`

Persists configuration changes to file.

```python
def write_active_config_to_toml(config: dict, toml_path: str) -> None:
    """
    Write configuration to TOML file.

    Args:
        config: Configuration dictionary to save
        toml_path: Output file path
    """
```

---

### `build_llama_eval_kwargs()`

Builds evaluation parameters for LLaMA models.

```python
def build_llama_eval_kwargs(
    model_name: str,
    precision_config: dict,
    **kwargs
) -> dict:
    """
    Build keyword arguments for LLaMA evaluation.

    Args:
        model_name: HuggingFace model identifier
        precision_config: Precision settings

    Returns:
        Kwargs dictionary for simulator
    """
```
