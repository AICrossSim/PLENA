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
endpackage

`endif
