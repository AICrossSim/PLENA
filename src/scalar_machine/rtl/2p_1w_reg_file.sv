
`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Scalar Register File
Timing      : Conbinatorial for read process, 1 cycle for write process
Statuscc
*/


module 2p_1w_reg_file #(
    parameter int BITWIDTH = 32,
    parameter int DEPTH = 32,
    localparam int ADDR_WIDTH = $clog2(DEPTH)
)(
    input  logic                  clk,
    input  logic                  we,               // Write enable
    input  logic [ADDR_WIDTH-1:0] waddr,            // Write address
    input  logic [BITWIDTH-1:0]   wdata,            // Write data
    input  logic [ADDR_WIDTH-1:0] raddr1,           // Read address port 1
    input  logic [ADDR_WIDTH-1:0] raddr2,           // Read address port 2
    output logic [BITWIDTH-1:0]   rdata1,           // Read data port 1
    output logic [BITWIDTH-1:0]   rdata2            // Read data port 2
);

    // Memory declaration
    logic [BITWIDTH-1:0] mem [0:DEPTH-1];

    // Write logic
    always_ff @(posedge clk) begin
        if (we) begin
            mem[waddr] <= wdata;
        end
    end

    // Read logic with forwarding
    always_comb begin
        if (we && (raddr1 == waddr)) begin
            rdata1 = wdata;  // Forwarding logic
        end else begin
            rdata1 = mem[raddr1];
        end

        if (we && (raddr2 == waddr)) begin
            rdata2 = wdata;  // Forwarding logic
        end else begin
            rdata2 = mem[raddr2];
        end
    end

endmodule
