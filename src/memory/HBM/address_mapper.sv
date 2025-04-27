`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Address Mapper
Timing      : Combinatorial
Description : This module mapping the computed addr to the address for HBM
*/


module address_mapper #(
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 32,
    parameter HBM_ADDR_WIDTH = 64,
    parameter HBM_DATA_WIDTH = 128
)(
    // Address Mapping Control
    input   logic [ADDR_WIDTH - 1 : 0] addr_in,

    // HBM Address Mapping
    output  logic [HBM_ADDR_WIDTH - 1 : 0] hbm_addr_out,
);

endmodule