`ifndef CONFIGURATION_SVH
`define CONFIGURATION_SVH

package configuration_pkg;
    parameter   BATCH_SIZE                      = 1;
    parameter   MLEN                            = 32;
    parameter   Matrix_Parallel_Rd_Dim          = 16;
    parameter   MATRIX_SRAM_DEPTH               = 128;
    parameter   VLEN                            = 32;
    parameter   SCRATCHPAD_SRAM_DEPTH           = 128;
    parameter   INST_BUFF_DEPTH                 = 8;
    parameter   ON_CHIP_ADDR_WIDTH              = 32;
    parameter   HBM_ADDR_WIDTH                  = 64;
    parameter   ADR_OPERAND_WIDTH               = 3;
    parameter   HBM_ADDR_REG_NUM                = 8;
    parameter   SourceWidth                     = 1;
    parameter   SinkWidth                       = 1;
    parameter   HBM_ELE_WIDTH                   = 8192;
    parameter   HBM_SCALE_WIDTH                 = 4096;
    parameter   FIXED_SRAM_DEPTH                = 32;
    parameter   FP_SRAM_DEPTH                   = 32;
endpackage

package pipeline_pkg;
    parameter   MAX_PIPELINE_STAGE             = 10;   
    parameter   PREFETCH_STAGE_1_CYCLES        = 2;
    parameter   MATRIX_MAX_CYCLES              = 8;
    parameter   MATRIX_LOADING_CYCLES          = 2;
    parameter   MATRIX_WO_OFFSET_CYCLES        = 6;
    parameter   MATRIX_W_OFFSET_CYCLES         = 8;
    parameter   VECTOR_MAX_CYCLES              = 6;
    parameter   VECTOR_BASIC_CYCLES            = 1;
    parameter   VECTOR_EXP_CYCLES              = 6;
    parameter   VECTOR_REDUCT_CYCLES           = 4;
    parameter   SCALAR_FP_MAX_CYCLES           = 4;
    parameter   SCALAR_FP_SQRT_CYCLES          = 2;
endpackage

`ifdef SIMULATION
    package simulation_pkg;
        parameter   BATCH_SIZE                      = 1;
        parameter   SourceWidth                     = 1;
        parameter   SinkWidth                       = 1;
        parameter   HBM_ELE_WIDTH                   = 8192; // In Bits
        parameter   HBM_SCALE_WIDTH                 = 8192; // In Bits
        parameter   HBM_ADDR_WIDTH                  = 64;
        parameter   FAKE_HBM_ADDR_WIDTH             = 4;
    endpackage
`endif



`endif
