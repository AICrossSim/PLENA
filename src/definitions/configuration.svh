`ifndef CONFIGURATION_SVH
`define CONFIGURATION_SVH
`include "global_define.vh"
`include "precision.svh"

import precision_pkg::*;

package configuration_pkg;
    parameter   BLEN = 4;
    parameter   MLEN = 8;
    parameter   Matrix_Parallel_Rd_Dim = 1;
    parameter   VLEN = 8;
    parameter   INST_BUFF_DEPTH = 8;
    parameter   ON_CHIP_ADDR_WIDTH = 32;
    parameter   HBM_ADDR_WIDTH = 64;
    parameter   ADR_OPERAND_WIDTH = 3;
    parameter   HBM_ADDR_REG_NUM = 8;
    parameter   SourceWidth = 1;
    parameter   SinkWidth = 1;
    parameter   MATRIX_ACC_ADR_DEPTH = 8;
    // Memory Related
    parameter   MATRIX_SRAM_WIDTH               = (LOW_MXFP_MANT_WIDTH + LOW_MXFP_EXP_WIDTH + 1 + MXFP_SCALE_WIDTH) * MLEN;
    parameter   MATRIX_SRAM_DEPTH = 128;
    parameter   VECTOR_SRAM_WIDTH               = (V_FP_MANT_WIDTH + V_FP_EXP_WIDTH + 1) * VLEN;
    parameter   VECTOR_SRAM_DEPTH = 128;
    parameter   FIXED_SRAM_WIDTH                = FIXED_DATA_WIDTH;
    parameter   FIXED_SRAM_DEPTH = 32;
    parameter   FP_SRAM_WIDTH                   = (S_FP_MANT_WIDTH + S_FP_EXP_WIDTH + 1);
    parameter   FP_SRAM_DEPTH = 32;
    // HBM Related
    parameter   HBM_M_Prefetch_Amount = 8;
    parameter   HBM_V_Prefetch_Amount = 8;
    parameter   HBM_V_Writeback_Amount = 8;
    parameter   HBM_ELE_WIDTH = 256;
    parameter   HBM_SCALE_WIDTH = 256;
endpackage

package simulation_pkg;
    parameter   FAKE_HBM_ADDR_WIDTH             = 16;
endpackage


package pipeline_pkg;
    parameter   MAX_PIPELINE_STAGE             = 10;   
    parameter   PREFETCH_STAGE_1_CYCLES        = 2;
    parameter   MATRIX_MAX_CYCLES              = 8;
    parameter   MATRIX_LOADING_CYCLES          = 2;
    parameter   MATRIX_WO_OFFSET_CYCLES        = 6;
    parameter   MATRIX_W_OFFSET_CYCLES         = 8;
    parameter   SYSTOLIC_PROCESSING_OVERHEAD   = 0;
    parameter   VECTOR_MAX_CYCLES              = 6;
    parameter   VECTOR_BASIC_CYCLES            = 1;
    parameter   VECTOR_EXP_CYCLES              = 6;
    parameter   VECTOR_REDUCT_CYCLES           = 4;
    parameter   SCALAR_FP_MAX_CYCLES           = 4;
    parameter   SCALAR_FP_SQRT_CYCLES          = 2;
endpackage


`endif
