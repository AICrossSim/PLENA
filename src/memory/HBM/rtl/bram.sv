`timescale 1ns / 1ps
module bram #(
    parameter DATA_WIDTH = 64,
    parameter ADDR_WIDTH = 20,
    parameter INIT_FILE  = ""
)(
    input  logic                  clk,
    input  logic                  bram_en_o,      // Enable signal
    input  logic [ADDR_WIDTH-1:0] bram_addr_o,    // Address
    input  logic [DATA_WIDTH-1:0] bram_wdata_o,   // Write data
    input  logic [7:0]            bram_wmask_o,   // Write mask (8 bytes for 64-bit)
    output logic [DATA_WIDTH-1:0] bram_rdata_i    // Read data
);

    // Memory declaration
    logic [DATA_WIDTH-1:0] memory [0:(1 << ADDR_WIDTH)-1];

    // Internal read data signal
    logic [DATA_WIDTH-1:0] read_data;

    // Byte-wise write
    always_ff @(posedge clk) begin
        if (bram_en_o) begin
            // Perform write if write mask has any bit set
            for (int i = 0; i < DATA_WIDTH/8; i++) begin
                if (bram_wmask_o[i])
                    memory[bram_addr_o][8*i +: 8] <= bram_wdata_o[8*i +: 8];
            end
            // Read happens regardless of write
            read_data <= memory[bram_addr_o];
        end
    end

    assign bram_rdata_i = read_data;

    // Load memory from file
    initial begin
        string filename;
        $sformat(filename, "%s", INIT_FILE);
        $display("Loading memory from: %s", filename);
        $readmemh(filename, memory);
    end

endmodule
