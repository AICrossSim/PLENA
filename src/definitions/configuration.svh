`ifndef CONFIGURATION_SVH
`define CONFIGURATION_SVH
`include "global_define.vh"
`include "precision.svh"

import precision_pkg::*;

package configuration_pkg;
    // Compute Unit Related
    localparam   BLEN = 8; // 4
    localparam   HLEN = 8;
    localparam   MLEN = 64; // 16
    localparam   Matrix_Parallel_Rd_Dim = 1;
    localparam   VLEN = 64; // 16
    localparam   INST_BUFF_DEPTH = 16;
    localparam   ON_CHIP_ADDR_WIDTH = precision_pkg::INT_DATA_WIDTH;
    // SourceWidth must satisfy: SourceWidth + SubbeatBits <= DeviceSourceWidth
    // where SubbeatBits = $clog2(HBM_WIDTH/32) for 32-bit host bus
    // Formula: base (2) + $clog2(HBM_WIDTH/32) + margin (2)
    localparam   SourceWidth = 4 + $clog2((precision_pkg::WT_MX_MANT_WIDTH + precision_pkg::WT_MX_EXP_WIDTH + 1) * MLEN / 16);  // [original: 5, tested: 6]
    localparam   SinkWidth = 1;
    // Memory Related
    localparam   MATRIX_SRAM_WIDTH = (precision_pkg::WT_MX_MANT_WIDTH + precision_pkg::WT_MX_EXP_WIDTH + 1 + precision_pkg::MX_SCALE_WIDTH) * MLEN;
    localparam   MATRIX_SRAM_DEPTH = 1024; // must be > 2x MLEN
    localparam   VECTOR_SRAM_WIDTH = (precision_pkg::V_FP_MANT_WIDTH + precision_pkg::V_FP_EXP_WIDTH + 1) * VLEN;
    localparam   VECTOR_SRAM_DEPTH = 1024; // must be > HEAD_DIM + HIDDEN_DIM/VLEN
    localparam   VECTOR_RESET_AMOUNT = 8;            // Need to be the same as Head_Dim for assembly code.
    localparam   INT_SRAM_WIDTH      = precision_pkg::INT_DATA_WIDTH;
    localparam   INT_SRAM_DEPTH      = 32;
    localparam   FP_SRAM_WIDTH       = (precision_pkg::S_FP_MANT_WIDTH + precision_pkg::S_FP_EXP_WIDTH + 1);
    localparam   FP_SRAM_DEPTH       = 512;
    localparam   HBM_ADDR_WIDTH      = 128;

    // HBM Related (calculated from precision parameters)
    localparam   HBM_M_Prefetch_Amount   = 16;
    localparam   HBM_V_Prefetch_Amount   = 16;
    localparam   HBM_V_Writeback_Amount  = 4;
    // Element width: (mant + exp + sign) * MLEN
    localparam   HBM_ELE_WIDTH_RAW       = (precision_pkg::WT_MX_MANT_WIDTH + precision_pkg::WT_MX_EXP_WIDTH + 1) * MLEN;
    // Round up to next power of 2 >= 2*raw (ensures power-of-2 for TileLink)
    // For original (4-bit): 256 raw -> 512
    // For tested (14-bit): 896 raw -> 2048
    localparam   HBM_ELE_WIDTH           = (1 << $clog2(HBM_ELE_WIDTH_RAW * 2));
    localparam   HBM_SCALE_WIDTH         = precision_pkg::MX_SCALE_WIDTH * (MLEN / precision_pkg::BLOCK_DIM);
    localparam   HBM_WIDTH               = HBM_ELE_WIDTH;
endpackage

package instruction_pkg;
    localparam INT_OPERAND_WIDTH     = 4;
    localparam FP_OPERAND_WIDTH      = 3;
    localparam HBM_ADR_OPERAND_WIDTH = 3;
    localparam STRIDE_OPERAND_WIDTH  = 3;
    localparam OPERAND_WIDTH         = 4;
    localparam FUNCT_WIDTH           = 4;
    localparam OPCODE_WIDTH          = 6;
    localparam IMM_WIDTH             = 22;
    localparam IMM_2_WIDTH           = 18;
    localparam INSTRUCTION_LENGTH    = 32;
endpackage

package simulation_pkg;
    localparam   FAKE_HBM_ADDR_WIDTH             = 16;
endpackage

`ifdef DC_LIB_EN // Define for DC Library Enabled, the pipeline stage lib changed accordingly.

    package pipeline_pkg;
        localparam   MAX_PIPELINE_STAGE             = 10;
        localparam   SYSTOLIC_PROCESSING_OVERHEAD   = 0;
        localparam   VECTOR_LONGEST_OPERATE_CYCLES  = 10;
        localparam   VECTOR_ADD_CYCLES              = 2;
        localparam   VECTOR_MUL_CYCLES              = 1;
        localparam   VECTOR_EXP_CYCLES              = 1;
        localparam   VECTOR_PREFIX_SCAN_CYCLES      = 9;
        localparam   VECTOR_SHIFT_CYCLES            = 1;
        localparam   VECTOR_RECI_CYCLES             = 2;
        localparam   VECTOR_MAX_CYCLES              = 4;
        localparam   VECTOR_SUM_CYCLES              = 8;
        localparam   SCALAR_FP_LONGEST_OPERATE_CYCLES = 4;
        localparam   SCALAR_FP_BASIC_CYCLES         = 1;
        localparam   SCALAR_FP_EXP_CYCLES           = 1;
        localparam   SCALAR_FP_SQRT_CYCLES          = 1;
        localparam   SCALAR_FP_RECI_CYCLES          = 1;
        localparam   SCALAR_INT_BASIC_CYCLES        = 1;
        localparam   HADAMARD_TRANSFORM_CYCLES      = $clog2(configuration_pkg::MLEN) + 1;
    endpackage

`else

    package pipeline_pkg;
        localparam   MAX_PIPELINE_STAGE             = 10;
        localparam   SYSTOLIC_PROCESSING_OVERHEAD   = 0;
        localparam   VECTOR_LONGEST_OPERATE_CYCLES  = 20;
        localparam   VECTOR_ADD_CYCLES              = 7;
        localparam   VECTOR_MUL_CYCLES              = 5;
        localparam   VECTOR_PREFIX_SCAN_CYCLES      = 9;
        localparam   VECTOR_EXP_CYCLES              = 6;
        localparam   VECTOR_SHIFT_CYCLES            = 1;
        localparam   VECTOR_RECI_CYCLES             = 7;
        localparam   VECTOR_MAX_CYCLES              = 4;
        localparam   VECTOR_SUM_CYCLES              = 20;
        localparam   SCALAR_FP_LONGEST_OPERATE_CYCLES = 4;
        localparam   SCALAR_FP_BASIC_CYCLES         = 1;
        localparam   SCALAR_FP_EXP_CYCLES           = 2;
        localparam   SCALAR_FP_SQRT_CYCLES          = 2;
        localparam   SCALAR_FP_RECI_CYCLES          = 2;
        localparam   SCALAR_INT_BASIC_CYCLES        = 1;
    endpackage

`endif

`endif