`timescale 1ns / 1ps
`include "global_define.vh"

/*
Module      : FP Per Tile Hadamard Transform RTL 
Timing      : Sequential Logic
Description : Full Pipelined Version Hadamard Transform RTL
Status      : Under Development
*/


module per_tile_hadamard_transform #(
    parameter   TILESIZE    = 4, 
    parameter   EXP_WIDTH   = 5,
    parameter   MANT_WIDTH  = 10
) (
    input  logic clk,
    input  logic rst,
    input  logic data_in_valid,
    input  logic [TILESIZE - 1: 0][EXP_WIDTH + MANT_WIDTH : 0] data_in,
    output logic data_out_valid,
    output logic [TILESIZE - 1: 0][EXP_WIDTH + MANT_WIDTH : 0] data_out
);

    localparam int TRANSFORM_STAGES = $clog2(TILESIZE);
    logic [TRANSFORM_STAGES + 1 : 0][TILESIZE - 1: 0][EXP_WIDTH + MANT_WIDTH : 0] data_reg;
    logic [TILESIZE - 1: 0][EXP_WIDTH + MANT_WIDTH : 0] stage_0_reg;
    logic [TRANSFORM_STAGES : 0] data_valid_reg;

    always_ff @(posedge clk) begin
        if (rst) begin
            data_valid_reg <= 1'b0;
            stage_0_reg    <= '0;
        end else begin
            if (data_in_valid) begin
                stage_0_reg         <= data_in;
                data_valid_reg[0]   <= 1'b1;
            end else begin
                stage_0_reg         <= '0;
                data_valid_reg[0]   <= 1'b0;
            end
            for (int i = 0; i < TRANSFORM_STAGES; i++) begin
                data_valid_reg[i + 1] <= data_valid_reg[i];
            end
        end
    end
    
    // Pipeline registers for each stage
    assign data_reg[0] = stage_0_reg;
    genvar h, i, j;
    generate
        for (h = 1; h < TILESIZE + 1; h *= 2) begin : loop_h
            localparam int STAGE = $clog2(h+1);
            for (i = 0; i < TILESIZE; i += h * 2) begin : loop_i
                for (j = i; j < i + h; j ++) begin
                    logic [EXP_WIDTH + MANT_WIDTH : 0] negated_data_b;
                    assign negated_data_b = {~data_reg[STAGE][j+h][EXP_WIDTH + MANT_WIDTH], 
                                            data_reg[STAGE][j+h][EXP_WIDTH + MANT_WIDTH - 1:0]};
                    fp_fix_adder_wo_handshake #(
                        .EXP_WIDTH(EXP_WIDTH),
                        .MANT_WIDTH(MANT_WIDTH)
                    ) fp_add (
                        .clk(clk),
                        .rst(rst),
                        .data_in_valid  (data_valid_reg[STAGE]),
                        .data_a         (data_reg[STAGE][j]),
                        .data_b         (data_reg[STAGE][j + h]),
                        .data_out       (data_reg[STAGE + 1][j]),
                        .data_out_valid()
                    );
                    
                    fp_fix_adder_wo_handshake #(
                        .EXP_WIDTH(EXP_WIDTH),
                        .MANT_WIDTH(MANT_WIDTH)
                    ) fp_sub (
                        .clk(clk),
                        .rst(rst),
                        .data_in_valid  (data_valid_reg[STAGE]),
                        .data_a         (data_reg[STAGE][j]),
                        .data_b         (negated_data_b),
                        .data_out       (data_reg[STAGE + 1][j + h]),
                        .data_out_valid ()
                    );
                end              
            end
        end
    endgenerate

    // Output assignment
    assign data_out         = data_reg[TRANSFORM_STAGES];
    assign data_out_valid   = data_valid_reg[TRANSFORM_STAGES];

endmodule