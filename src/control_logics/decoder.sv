`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Decoder
Timing      : Conbinatorial
Statuscc
*/

module vector_operation_control #(
    input  CUSTOM_ISA_OPCODE        opcode,

    // Data Pre-Fetching from HBM

    // Data Retrieval from Memory

    // Operation Control
    

    // Vector Control
    output V_ELEMENT_OP      element_opcode,
    output V_REDUCT_OP       red_opcode
);
    
endmodule