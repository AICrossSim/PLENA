# Kernel Agents

## Setup
```bash
export ANTHROPIC_API_KEY="your-api-key"
```

## Run Agent
```bash
python kernel_agents/run_agent.py "Generate FFN assembly for llama-3.2-1b"
python kernel_agents/run_agent.py --interactive
```

## Test Tools
```bash
python kernel_agents/test_tools.py                    # all tools
python kernel_agents/test_tools.py -t get_doc
python kernel_agents/test_tools.py -t get_workload
python kernel_agents/test_tools.py -t get_template
python kernel_agents/test_tools.py -t setup_test_environment
python kernel_agents/test_tools.py -t run_simulator
```

## Python API
```python
from kernel_agents.anthropic_agent.tools import (
    get_doc, get_workload, get_template,
    setup_test_environment, run_simulator
)

env = setup_test_environment(hidden_size=128, batch_size=4)
result = run_simulator(env['assembly_code'])
# {'success': True, 'latency_ns': 4943.0, 'mse': 1.25, ...}
```
