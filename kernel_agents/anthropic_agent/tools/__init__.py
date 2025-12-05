"""Tools for the anthropic agent."""

from .examples import get_assembly_code_examples
from .machine_code import machine_code_generation
from .simulator import run_simulator, setup_test_environment
from .instruction_size import get_instruction_size
from .template import get_template
from .doc import get_doc
from .workload import get_workload

__all__ = [
    "get_assembly_code_examples",
    "machine_code_generation",
    "run_simulator",
    "setup_test_environment",
    "get_instruction_size",
    "get_template",
    "get_doc",
    "get_workload",
]
