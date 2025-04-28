`ifdef CONFIGURATION_SVH
`define CONFIGURATION_SVH

parameter   BATCH_SIZE                      = 1;

parameter   MLEN                            = 16;
parameter   Matrix_Parallel_Rd_Dim          = 2;
parameter   MATRIX_SRAM_DEPTH               = 128;


parameter   VLEN                            = 16;
parameter   SCRATCHPAD_SRAM_DEPTH           = 128;



`endif