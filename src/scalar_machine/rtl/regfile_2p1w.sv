
`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Scalar Register File
Timing      : 1 cycle for read process, 1 cycle for write process
*/


module regfile_2p1w #(
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

    initial begin
        // Initialize memory to zero
        for (int i = 0; i < DEPTH; i++) begin
            mem[i] = '0;
        end
    end

    
    always_ff @(posedge clk) begin
        // Read logic
        if (raddr1 == waddr && we) begin
            rdata1 <= wdata; // If reading from the same address being written to, return the new data
        end else begin
            rdata1 <= (raddr1 == 0) ? '0 : mem[raddr1]; // Return zero for address 0
        end
        if (raddr2 == waddr && we) begin
            rdata2 <= wdata; // If reading from the same address being written to, return the new data
        end else begin
            rdata2 <= (raddr2 == 0) ? '0 : mem[raddr2]; // Return zero for address 0
        end

        // Write logic
        if (we) begin
            // assert (waddr != 0) else $error("Attempting to write to address 0");
            if (waddr != 0) begin  // Avoid writing to address 0
                mem[waddr] <= wdata;
            end
        end
    end

endmodule
