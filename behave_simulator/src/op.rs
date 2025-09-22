#[derive(Debug, Clone, Copy)]
pub enum MatrixPrecision {
    Weights,
    KeyValue,
}

#[derive(Debug, Clone, Copy)]
pub enum VectorPrecision {
    Activation,
    KeyValue,
}

#[derive(Debug)]
pub enum Opcode {
    Invalid,

    MMm {
        rs1: u8,
        rs2: u8,
    },
    MTmm {
        rs1: u8,
        rs2: u8,
    },
    MMmWo {
        rd: u8,
        imm: u32,
    },
    MMv {
        rs1: u8,
        rs2: u8,
    },
    MTmv {
        rs1: u8,
        rs2: u8,
    },
    MMvWo {
        rd: u8,
        imm: u32,
    },

    VAddVv {
        rd: u8,
        rs1: u8,
        rs2: u8,
    },
    VAddVf {
        rd: u8,
        rs1: u8,
        rs2: u8,
    },
    VSubVv {
        rd: u8,
        rs1: u8,
        rs2: u8,
    },
    VSubVf {
        rd: u8,
        rs1: u8,
        rs2: u8,
    },
    VMulVv {
        rd: u8,
        rs1: u8,
        rs2: u8,
    },
    VMulVf {
        rd: u8,
        rs1: u8,
        rs2: u8,
    },
    VExpV {
        rd: u8,
        rs1: u8,
    },
    VReciV {
        rd: u8,
        rs1: u8,
    },
    VBcF {
        rd: u8,
        rs1: u8,
    },
    VRedSum {
        rd: u8,
        rs1: u8,
    },
    VRedMax {
        rd: u8,
        rs1: u8,
    },

    SAddFp {
        rd: u8,
        rs1: u8,
        rs2: u8,
    },
    SSubFp {
        rd: u8,
        rs1: u8,
        rs2: u8,
    },
    SMaxFp {
        rd: u8,
        rs1: u8,
        rs2: u8,
    },
    SMulFp {
        rd: u8,
        rs1: u8,
        rs2: u8,
    },
    SExpFp {
        rd: u8,
        rs1: u8,
    },
    SReciFp {
        rd: u8,
        rs1: u8,
    },
    SSqrtFp {
        rd: u8,
        rs1: u8,
    },
    SLdFp {
        rd: u8,
        rs1: u8,
        imm: u32,
    },
    SStFp {
        rd: u8,
        rs1: u8,
        imm: u32,
    },
    SMapVFp {
        rd: u8,
        rs1: u8,
        imm: u32,
    },

    SAddInt {
        rd: u8,
        rs1: u8,
        rs2: u8,
    },
    SAddiInt {
        rd: u8,
        rs1: u8,
        imm: u32,
    },
    SSubInt {
        rd: u8,
        rs1: u8,
        rs2: u8,
    },
    SMulInt {
        rd: u8,
        rs1: u8,
        rs2: u8,
    },
    SLuiInt {
        rd: u8,
        imm: u32,
    },
    SLdInt {
        rd: u8,
        rs1: u8,
        imm: u32,
    },
    SStInt {
        rd: u8,
        rs1: u8,
        imm: u32,
    },

    HPrefetchM {
        rd: u8,
        rs1: u8,
        rs2: u8,
        rstride: u8,
        precision: MatrixPrecision,
    },
    HPrefetchV {
        rd: u8,
        rs1: u8,
        rs2: u8,
        rstride: u8,
        precision: VectorPrecision,
    },
    HStoreV {
        rd: u8,
        rs1: u8,
        rs2: u8,
        rstride: u8,
        precision: VectorPrecision,
    },

    CSetAddrReg {
        rd: u8,
        rs1: u8,
        rs2: u8,
    },
    CSetScaleReg {
        rd: u8,
    },
    CBreak,
}

const OPERAND_WIDTH: u32 = 4;
const OPCODE_WIDTH: u32 = 6;
const IMM_WIDTH: u32 = 22;
const IMM_2_WIDTH: u32 = 18;

const fn mask(width: u32) -> u32 {
    ((1 << width) - 1) as u32
}

impl Opcode {
    pub fn decode(instr: u32) -> Self {
        eprintln!(
            "decode(): instr = 0x{instr:08X} ({instr:032b})"
        );
        let opcode = instr & mask(OPCODE_WIDTH);
        let rd = ((instr >> OPCODE_WIDTH) & mask(OPERAND_WIDTH)) as u8;
        let rs1 = ((instr >> (OPCODE_WIDTH + OPERAND_WIDTH)) & mask(OPERAND_WIDTH)) as u8;
        let rs2 = ((instr >> (OPCODE_WIDTH + OPERAND_WIDTH * 2)) & mask(OPERAND_WIDTH)) as u8;
        let rs3 = ((instr >> (OPCODE_WIDTH + OPERAND_WIDTH * 3)) & mask(OPERAND_WIDTH)) as u8;
        let imm = ((instr >> (OPCODE_WIDTH + OPERAND_WIDTH)) & mask(IMM_WIDTH)) as u32;
        let imm2 = ((instr >> (OPCODE_WIDTH + OPERAND_WIDTH * 2)) & mask(IMM_2_WIDTH)) as u32;

        match opcode {
            0x00 => Self::Invalid,

            0x01 => Self::MMm { rs1, rs2 },
            0x02 => Self::MTmm { rs1, rs2 },
            0x03 => Self::MMmWo { rd, imm: imm2 },
            0x04 => Self::MMv { rs1, rs2 },
            0x05 => Self::MMvWo { rd, imm: imm2 },
            0x06 => Self::MTmv { rs1, rs2 },

            0x07 => Self::VAddVv { rd, rs1, rs2 },
            0x08 => Self::VAddVf { rd, rs1, rs2 },
            0x09 => Self::VSubVv { rd, rs1, rs2 },
            0x0A => Self::VSubVf { rd, rs1, rs2 },
            0x0B => Self::VMulVv { rd, rs1, rs2 },
            0x0C => Self::VMulVf { rd, rs1, rs2 },
            0x0D => Self::VExpV { rd, rs1 },
            0x0E => Self::VReciV { rd, rs1 },
            0x0F => Self::VBcF { rd, rs1 },
            0x10 => Self::VRedSum { rd, rs1 },
            0x11 => Self::VRedMax { rd, rs1 },

            0x12 => Self::SAddFp { rd, rs1, rs2 },
            0x13 => Self::SSubFp { rd, rs1, rs2 },
            0x14 => Self::SMaxFp { rd, rs1, rs2 },
            0x15 => Self::SMulFp { rd, rs1, rs2 },
            0x16 => Self::SExpFp { rd, rs1 },
            0x17 => Self::SReciFp { rd, rs1 },
            0x18 => Self::SSqrtFp { rd, rs1 },
            0x19 => Self::SLdFp { rd, rs1, imm: imm2 },
            0x1A => Self::SStFp { rd, rs1, imm: imm2 },
            0x1B => Self::SMapVFp { rd, rs1, imm: imm2 },

            0x1C => Self::SAddInt { rd, rs1, rs2 },
            0x1D => Self::SAddiInt { rd, rs1, imm: imm2 },
            0x1E => Self::SSubInt { rd, rs1, rs2 },
            0x1F => Self::SMulInt { rd, rs1, rs2 },
            0x20 => Self::SLuiInt { rd, imm },
            0x21 => Self::SLdInt { rd, rs1, imm: imm2 },
            0x22 => Self::SStInt { rd, rs1, imm: imm2 },

            0x23 => Self::HPrefetchM {
                rd,
                rs1,
                rs2,
                rstride: rs3,
                precision: MatrixPrecision::Weights,
            },
            // 0x2A => Self::HPrefetchM { rd, rs1, rs2, rstride: rs3, precision: MatrixPrecision::KeyValue },
            0x24 => Self::HPrefetchV {
                rd,
                rs1,
                rs2,
                rstride: rs3,
                precision: VectorPrecision::KeyValue,
            },
            // 0x2E => Self::HPrefetchV { rd, rs1, rs2, rstride: rs3, precision: VectorPrecision::KeyValue },
            0x25 => Self::HStoreV {
                rd,
                rs1,
                rs2,
                rstride: rs3,
                precision: VectorPrecision::Activation,
            },
            // 0x32 => Self::HStoreV { rd, rs1, rs2, rstride: rs3, precision: VectorPrecision::KeyValue },
            0x26 => Self::CSetAddrReg { rd, rs1, rs2 },
            0x27 => Self::CSetScaleReg { rd },

            // 0x28 => Self::CHadamardTransform,
            0x29 => Self::CBreak,

            _ => {
                eprintln!("Unknown opcode {opcode:#x}");
                Self::Invalid
            }
        }
    }
}
