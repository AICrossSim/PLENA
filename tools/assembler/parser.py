import re
from typing import List, Optional

def load_isa_definitions(file_path: str) -> dict:
    """
    Parse a SystemVerilog enum from a .svh file and return it as a dictionary.
    """
    enum_dict = {}
    inside_enum = False
    pattern = re.compile(r'(\w+)\s*=\s*(\d+)\'h([0-9A-Fa-f]+)')

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()

            # Detect the start of the enum
            if line.startswith(f'typedef enum') and 'OPCODE_WIDTH' in line:
                inside_enum = True
                continue

            if inside_enum:
                # End of enum
                if line.endswith('} CUSTOM_ISA_OPCODE;'):
                    break

                # Match line like: S_ADD_FP = 6'h0E,
                match = pattern.search(line)
                if match:
                    name = match.group(1)
                    value = int(match.group(3), 16)
                    enum_dict[name] = value

    return enum_dict

def load_isa_settings(file_path: str) -> dict:
    param_pattern = re.compile(r'parameter\s+(\w+)\s*=\s*([^;]+);')
    param_dict = {}
    isa_settings_param = ["OPERAND_WIDTH", "OPCODE_WIDTH", "IMM_WIDTH", "IMM_2_WIDTH"]
    # First pass: collect simple constant values
    with open(file_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if line.startswith('//') or not line or 'parameter' not in line:
            continue

        match = param_pattern.match(line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()

            if key not in isa_settings_param:
                continue

            # Try to resolve constant integer values
            try:
                param_dict[key] = int(value)
            except ValueError:
                param_dict[key] = value  # Expression, to evaluate later
    return param_dict


class Instruction:
    def __init__(self, opcode: str, rd: str, rs1: Optional[str], rs2: Optional[str], imm: Optional[int]):
        self.opcode = opcode
        self.rd = rd
        self.rs1 = rs1
        self.rs2 = rs2
        self.imm = imm

    def __repr__(self):
        return f"Instruction(opcode='{self.opcode}', rd='{self.rd}', rs1='{self.rs1}', rs2='{self.rs2}', imm={self.imm})"


def parse_asm_file(file_path: str) -> List[Instruction]:
    """
    Parse an ASM file into a list of Instruction objects.

    Supported formats:
    - opcode rd, rs1, imm;
    - opcode rd, rs1, rs2;
    - opcode rd, rs1;
    - opcode rd;

    :param file_path: Path to the .asm file
    :return: List of Instruction objects
    """
    instructions = []

    with open(file_path, 'r') as file:
        for line in file:
            # Remove comments and strip whitespace
            line = line.split('//')[0].strip().rstrip(';')
            if not line:
                continue

            # Split the opcode and operands
            parts = line.split()
            if len(parts) < 2:
                continue  # Invalid line
            print(parts)
            opcode = parts[0]
            operands = [part.strip() for part in ' '.join(parts[1:]).split(',')]
            # Decode based on number of operands
            rd  = int(operands[0][1:], 16) if len(operands) > 0 else None
            rs1 = int(operands[1][1:], 16) if len(operands) > 1 else None
            rs2 = None
            imm = None

            if len(operands) == 3:
                if operands[2].startswith('x'):
                    rs2 = int(operands[2][1:], 16)
                else:
                    try:
                        imm = int(operands[2])
                    except ValueError:
                        pass

            instructions.append(Instruction(opcode, rd, rs1, rs2, imm))

    return instructions



if __name__ == "__main__":
    # Example usage
    # file_path = '/home/george/Coprocessor_for_Llama/src/definitions/operation.svh'
    # enum_dict = load_isa_definitions(file_path)
    # print(enum_dict)

    asm_file_path = '/home/george/Coprocessor_for_Llama/src/system/test/benchmarks/fixed.asm'
    loaded_instr = parse_asm_file(asm_file_path)
    for instr in loaded_instr:
        print(instr)