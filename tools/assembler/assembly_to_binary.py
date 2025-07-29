from assembler.parser import load_isa_definitions, load_isa_settings, parse_asm_file

from utils.load_config import load_svh_settings
import torch
from cfl_tools import PROJECT_PATH
from pathlib import Path
import argparse

class AssemblyToBinary:
    def __init__(self, isa_definition_file: str, config_file: str):
        """
        Initialize the Assembler with the ISA file.

        :param isa_definition_file: Path to the ISA file
        """
        self.isa_definitions = load_isa_definitions(isa_definition_file)
        self.isa_definition_file = isa_definition_file
        config_settings = load_svh_settings(config_file)
        self.opcode_width    = config_settings.get("OPCODE_WIDTH", 0)
        self.operands_width  = config_settings.get("OPERAND_WIDTH", 0)
        self.imm_width       = config_settings.get("IMM_WIDTH", 0)
        self.imm2_width      = config_settings.get("IMM_2_WIDTH", 0)
        self.instruction_length = config_settings.get("INSTRUCTION_LENGTH", 0)
        self.funct_width = config_settings.get("FUNCT_WIDTH", 0)
        self.funct_dist = self.instruction_length - 2 * self.funct_width


    def _convert_to_binary(self, instruction):
        """
        Convert an instruction to its binary representation.

        :param instruction: Instruction object
        :return: Binary representation of the instruction
        """
        # Example conversion logic (to be replaced with actual logic)
        opcode = self.isa_definitions[instruction.opcode]
        rd =  instruction.rd
        rs1 = instruction.rs1
        rs2 = instruction.rs2
        rstride = instruction.rstride
        funct1 = instruction.funct1
        imm = instruction.imm
        binary_instruction = 0
        print(f"Converting instruction: {instruction.opcode} with opcode={hex(opcode)}, rd={rd}, rs1={rs1}, rs2={rs2}, rstride={rstride}, funct1={funct1}, imm={imm}")
        ow = self.operands_width
        opw = self.opcode_width
        if instruction.opcode in ["S_ADDI_INT", "S_LD_FP", "S_ST_FP", "S_LD_INT", "S_ST_INT", "S_MAP_V_FP", "V_RED_SUM", "V_RED_MAX", "V_RECI_V", "V_EXP_V"]:
            binary_instruction = (
                (imm << (opw + 2 * ow)) +
                (rs1 << (opw + ow)) +
                (rd << opw) +
                opcode
            )
        elif instruction.opcode in ["S_LUI_INT", "C_SET_SCALE_REG"]:
            binary_instruction = (
                (imm << (opw + ow)) +
                (rd << opw) +
                opcode
            )
        elif instruction.opcode in [ "S_MV_FP", "S_RECI_FP", "S_EXP_FP", "S_SQRT_FP", "V_EXP_V"]:
            binary_instruction = (
                (rs1 << (opw + ow)) +
                (rd << opw) +
                opcode
            )
        elif instruction.opcode in [ "H_PREFETCH_M", "H_PREFETCH_V", "H_STORE_V"]:
            binary_instruction = (
                (funct1 << (opw + 4 * ow)) +
                (rstride << (opw + 3 * ow)) +
                (rs2 << (opw + 2 * ow)) +
                (rs1 << (opw + ow)) +
                (rd << opw) +
                opcode
            )
        else:
            binary_instruction = (
                (rs2 << (opw + 2 * ow)) +
                (rs1 << (opw + ow)) +
                (rd << opw) +
                opcode
            )

        # Print in hex with fixed 16-bit width
        return binary_instruction
    
    def write_binary_to_file(self, binary_instructions, output_file: str):
        with open(output_file, 'w') as file:
            for instruction in binary_instructions:
                file.write(f"0x{instruction:08X}\n")
    
    def generate_binary(self, asm_file: str, output_file: str):
        """
        Generate binary instructions from the assembled instructions.
        """
        instructions = parse_asm_file(asm_file)
        binary_instructions = []
        for instruction in instructions:
            # Convert each instruction to binary format
            binary_instruction = self._convert_to_binary(instruction)
            binary_instructions.append(binary_instruction)
        # Write the binary instructions to a file
        self.write_binary_to_file(binary_instructions, output_file)
        return binary_instructions
    

