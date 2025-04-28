`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Address Mapper
Timing      : Combinatorial
Description : This module mapping the computed addr to the address for HBM
Status      : Under Development
*/


module address_mapper #(
    parameter ADDR_WIDTH = 32,
    parameter ADR_OPERAND_WIDTH = 5,
    parameter HBM_ADDR_WIDTH = 64

)(
    input   logic clk,
    input   logic rst,

    // Address Mapping Control
    input   logic [ADDR_WIDTH - 1 : 0] addr_in_a,
    input   logic [ADDR_WIDTH - 1 : 0] addr_in_b,
    input   logic [ADR_OPERAND_WIDTH - 1 : 0] target_operand,

    // HBM Address Mapping
    output  logic [HBM_ADDR_WIDTH - 1 : 0] hbm_addr_out,
);


initial begin
    assert (HBM_ADDR_WIDTH >= 2 * ADDR_WIDTH) else $error("Address width is less than HBM address width");
end


endmodule