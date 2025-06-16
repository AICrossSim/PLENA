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
    parameter HBM_ADDR_WIDTH = 64,
    parameter HBM_ADDR_REG_NUM = 4,
    localparam  HBM_ADDR_OPERAND_WIDTH = $clog2(HBM_ADDR_REG_NUM)

)(
    input   logic clk,
    input   logic rst,

    // Control
    input   logic mapp_addr_en,
    input   logic set_addr_en,

    // Address Mapping
    input   logic [ADDR_WIDTH - 1 : 0] addr_in_a,
    input   logic [ADDR_WIDTH - 1 : 0] addr_in_b,
    input   logic [ADDR_WIDTH - 1 : 0] addr_offset,
    input   logic [ADR_OPERAND_WIDTH - 1 : 0] write_operand,
    input   logic [ADR_OPERAND_WIDTH - 1 : 0] read_operand,

    // HBM Address Mapping
    output  logic [HBM_ADDR_WIDTH - 1 : 0] hbm_addr_out
);


initial begin
    assert (HBM_ADDR_WIDTH >= 2 * ADDR_WIDTH) else $error("Address width is less than HBM address width");
end

logic [HBM_ADDR_WIDTH - 1 : 0] hbm_addr [HBM_ADDR_REG_NUM - 1 : 0];

always_ff @(posedge clk) begin
    if (rst) begin
        for (int i = 0; i < HBM_ADDR_REG_NUM; i++) begin
            hbm_addr[i] <= 'b0;
        end
    end else begin
        if (set_addr_en) begin
            hbm_addr[write_operand] <= {addr_in_a, addr_in_b};
        end
        if (mapp_addr_en) begin
            hbm_addr_out <= hbm_addr[read_operand] + {{HBM_ADDR_WIDTH - ADDR_WIDTH{1'b0}}, addr_offset};
        end else begin
            hbm_addr_out <= {HBM_ADDR_WIDTH{1'b0}};
        end
    end
end


endmodule