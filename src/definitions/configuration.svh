`ifndef CONFIGURATION_SVH
`define CONFIGURATION_SVH

package configuration_pkg;
    parameter   BATCH_SIZE                      = 1;
    parameter   MLEN                            = 4;
    parameter   Matrix_Parallel_Rd_Dim          = 2;
    parameter   MATRIX_SRAM_DEPTH               = 128;
    parameter   VLEN                            = 4;
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

package pipeline_pkg;
    parameter   MAX_PIPELINE_STAGE              = 10;   
    // typedef enum logic[1:0] { 
    //     STALL_M_SRAM = 2'b00,
    //     STALL_S_SRAM = 2'b01,
    //     STALL_S_REG = 2'b10,
    //     CLEAR   = 2'b11
    // } MEM_STALL_TYPE; 

    typedef struct {
        logic stall_m_sram;
        logic stall_s_sram;
        logic stall_s_reg;
    } MEM_STALL_TYPE;
    
endpackage


package simulation_pkg;
    parameter   BATCH_SIZE                      = 1;
    parameter   SourceWidth                     = 1;
    parameter   SinkWidth                       = 1;
    parameter   HBM_ELE_WIDTH                   = 128;
    parameter   HBM_SCALE_WIDTH                 = 128;
    parameter   HBM_ADDR_WIDTH                  = 64;
    parameter   FAKE_HBM_ADDR_WIDTH             = 4;
endpackage



`endif
