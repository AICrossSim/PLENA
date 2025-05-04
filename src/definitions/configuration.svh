`ifndef CONFIGURATION_SVH
`define CONFIGURATION_SVH

package configuration_pkg;
    parameter   BATCH_SIZE                      = 1;
    parameter   MLEN                            = 16;
    parameter   Matrix_Parallel_Rd_Dim          = 2;
    parameter   MATRIX_SRAM_DEPTH               = 128;
    parameter   VLEN                            = 16;
    parameter   SCRATCHPAD_SRAM_DEPTH           = 128;
    parameter   INST_BUFF_DEPTH                 = 8;
    parameter   HBM_ADDR_WIDTH                  = 64;
    parameter   ADR_OPERAND_WIDTH               = 3;
    parameter   HBM_ADDR_REG_NUM                = 8;
    parameter   SourceWidth                     = 1;
    parameter   SinkWidth                       = 1;
    parameter   HBM_ELE_WIDTH                   = 128;
    parameter   HBM_SCALE_WIDTH                 = 128;
endpackage


package simulation_pkg;
    parameter   BATCH_SIZE                      = 1;
    parameter   SourceWidth                     = 1;
    parameter   SinkWidth                       = 1;
    parameter   HBM_ELE_WIDTH                   = 128;
    parameter   HBM_SCALE_WIDTH                 = 128;
    parameter   HBM_ADDR_WIDTH                  = 64;
    parameter   FAKE_HBM_ADDR_WIDTH             = 16;
    
endpackage

`endif
