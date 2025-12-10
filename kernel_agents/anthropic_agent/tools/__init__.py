"""Tools for the anthropic agent."""

from .machine_code import machine_code_generation
from .simulator import run_simulator
from .instruction_size import get_instruction_size
from .doc import get_doc
from .workload import get_workload
from .debug import debug_view_memory
from .read_file import read_file

__all__ = [
    "machine_code_generation",
    "run_simulator",
    "get_instruction_size",
    "get_doc",
    "get_workload",
    "debug_view_memory",
    "read_file",
]
