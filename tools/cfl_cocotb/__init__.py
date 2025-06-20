from .runner import veri_runner
from .matrix_analyser import packed_array_analyser
from .fp_generation import FpGenerator
from .mx_fp_generation import MXBlockFPConverter

from pathlib import Path

RTL_PATH = Path(__file__).parents[2] / "src"