`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Scalar Register File
Timing      : 1 cycle for read process, 1 cycle for write process
Description : This module implements a 2-port, 1-read 1-write register file.
            ：This unit supports level 1 forwarding.
*/

module non_volatile_1p_storage #(
    parameter int BITWIDTH = 32,
    parameter int DEPTH = 32,
    `ifdef SIMULATION
        parameter string MemInitFile = "",
    `endif
    localparam int ADDR_WIDTH = $clog2(DEPTH)
)(
    input  logic                  clk,
    input  logic [ADDR_WIDTH-1:0] raddr,            // Read address
    output logic [BITWIDTH-1:0]   rdata             // Read data
);

`ifndef SYNTHESIS_MEMORY_BLACK_BOXING
    // Memory declaration
    logic [BITWIDTH-1:0] mem [0:DEPTH-1];

`ifdef SIMULATION
    initial begin
        string filename;
        $sformat(filename, "%s", MemInitFile);
        $display("Loading memory from: %s", filename);
        $readmemh(filename, mem);
    end
`endif

    always_ff @(posedge clk) begin
        rdata <= (raddr == 0) ? '1 : mem[raddr]; 
    end

`endif

endmodule
