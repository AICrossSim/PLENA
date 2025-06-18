`timescale 1ns / 1ps
module bram #(
    parameter DATA_WIDTH = 64,
    parameter ADDR_WIDTH = 20,
    parameter string INIT_FILE  = "",
    parameter string RESULT_FILE = "",
    localparam int MASK_WIDTH = DATA_WIDTH / 8
)(
    input  logic                  clk,
    input  logic                  bram_en_o,      // Enable signal
    input  logic                  bram_we_o,      // Write enable signal
    input  logic [ADDR_WIDTH-1:0] bram_addr_o,    // Address
    input  logic [DATA_WIDTH-1:0] bram_wdata_o,   // Write data
    input  logic [MASK_WIDTH-1:0] bram_wmask_o,   // Write mask (8 bytes for 64-bit)
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
            if (bram_we_o) begin
                // Write data to memory based on write mask
                for (int i = 0; i < DATA_WIDTH/8; i++) begin
                    if (bram_wmask_o[i]) begin
                        memory[bram_addr_o][8*i +: 8] <= bram_wdata_o[8*i +: 8];
                    end
                        
                end
            end else begin
                // If not writing, just read the data
                read_data <= memory[bram_addr_o];
            end
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

    // Load result file if specified
    final begin
        if (RESULT_FILE != "") begin
            string result_filename;
            $sformat(result_filename, "%s", RESULT_FILE);
            $display("Loading result file from: %s", result_filename);
            $writememh(result_filename, memory);
        end
    end

endmodule
