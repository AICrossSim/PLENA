import sys
from sympy.core.assumptions_generated import generated_assumptions
import torch
import pdb
import torch.nn as nn
import torch.nn.functional as F
import pdb
from bitstring import BitArray
from functools import partial
from pathlib import Path
from cfl_cocotb import RTL_PATH
from cfl_tools.logger import get_logger
logger = get_logger(__name__)

FUNCTION_TABLE = {
    "silu": nn.SiLU(),
    "elu": nn.ELU(),
    "sigmoid": nn.Sigmoid(),
    "logsigmoid": nn.LogSigmoid(),
    "softshrink": nn.Softshrink(),
    "gelu": nn.GELU(),
    "exp": torch.exp,
    "power2": lambda x: torch.pow(2, x),
    "softmax": torch.exp,
    "isqrt": torch.sqrt,
}

class GenerateSVLut:
    def __init__(self, function_name, save : bool = False):
        assert (
            function_name in FUNCTION_TABLE
        ), f"Function {function_name} not found in FUNCTION_TABLE"
        self.function_name = function_name
        self.f = FUNCTION_TABLE[function_name]
        self.save = save

    def pipeline(self):
        self.generate_lut()
        sv_code = self.generate_sv()
        if self.save:
            p = RTL_PATH / "generated_lut" / "rtl" / f"{self.function_name}_lut.sv"
            if not p.parent.exists():
                p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w") as file:
                file.write(sv_code)
            logger.info(f"SystemVerilog module generated and saved as {p}.")
        else:
            logger.info("Code was not saved to file.")
        return sv_code


    def generate_lut(self):
        self.lut_dict = {
            "in_entry_width": None,
            "out_entry_width": None,
            "quant_info": None,
            "lut": {},
        }
        return NotImplementedError

    def generate_sv(self):
        lut_dict = self.lut_dict
        function_name = self.function_name
        quant_info = lut_dict["quant_info"]
        in_entry_width = lut_dict["in_entry_width"]
        out_entry_width = lut_dict["out_entry_width"]
        dicto = lut_dict["lut"]
        # Format for bit sizing
        # Starting the module and case statement
        key_format = f"{in_entry_width}'b{{}}"
        value_format = f"{out_entry_width}'b{{}}"
        sv_code = f"""
`timescale 1ns / 1ps
/* verilator lint_off UNUSEDPARAM */
module {function_name}_lut #(
    parameter IN_ENTRY_WIDTH = {in_entry_width},
    parameter OUT_ENTRY_WIDTH = {out_entry_width},
)
(
// {quant_info}
    input logic [IN_ENTRY_WIDTH-1:0] data_in_0, 
    output logic [OUT_ENTRY_WIDTH-1:0] data_out_0
);
\n"""
        sv_code += "    always_comb begin\n"
        sv_code += "        case(data_in_0)\n"

        # Adding each case
        for key, value in dicto.items():
            formatted_key = key_format.format(key)
            formatted_value = value_format.format(value)
            sv_code += f"            {formatted_key}: data_out_0 = {formatted_value};\n"

        # Ending the case statement and module
        sv_code += f"            default: data_out_0 = {out_entry_width}'b0;\n"
        sv_code += "        endcase\n"
        sv_code += "    end\n"
        sv_code += "endmodule\n"

        return sv_code

if __name__ == "__main__":
    pass