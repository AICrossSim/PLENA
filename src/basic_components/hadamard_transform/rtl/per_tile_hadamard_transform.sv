`timescale 1ns / 1ps

/*
Module      : Per Tile Hadamard Transform RTL 
Timing      : Sequential Logic
Status      : Full Pipelined Version Hadamard Transform RTL
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
    logic [TRANSFORM_STAGES : 0][TILESIZE - 1: 0][EXP_WIDTH + MANT_WIDTH : 0] data_reg;
    logic [TRANSFORM_STAGES : 0][TILESIZE - 1: 0] data_valid_reg;
    logic [TRANSFORM_STAGES : 0][TILESIZE - 1: 0] data_ready_reg;

    always_ff begin
        if (rst) begin
            data_reg <= '0;
            data_valid_reg <= '0;
            data_ready_reg <= '0;
        end else begin
            if (data_in_valid) begin
                data_reg[0]         <= data_in;
                data_valid_reg[0]   <= 1'b1;
            end else begin
                data_valid_reg[0]   <= 1'b0;
                data_reg[0]         <= '0;
            end
        end
    end
    
    // Pipeline registers for each stage
    genvar h, i, j;

    generate
        for (h = 1; h < TILESIZE + 1; h = h * 2) begin : loop_h
            localparam int STAGE = $clog2(h+1);
            for (i = 0; i < TILESIZE; i = i + h) begin : loop_i
                for (j = i, j < i + h; j ++) begin
                    logic [EXP_WIDTH + MANT_WIDTH : 0] negated_data_b;
                    assign negated_data_b = {data_reg[STAGE][j+h][EXP_WIDTH + MANT_WIDTH], 
                                            ~data_reg[STAGE][j+h][EXP_WIDTH + MANT_WIDTH - 1:0]};
                    fp_fix_adder_wo_handshake #(
                        .EXP_WIDTH(EXP_WIDTH),
                        .MANT_WIDTH(MANT_WIDTH)
                    ) fp_add (
                        .clk(clk),
                        .rst(rst),
                        .data_in_valid  (data_in_valid_reg[STAGE]),
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
                        .data_in_valid  (data_in_valid_reg[STAGE]),
                        .data_a         (data_reg[STAGE][j]),
                        .data_b         (negated_data_b[STAGE][j + h]),
                        .data_out       (data_reg[STAGE + 1][j + h]),
                        .data_out_valid ()
                    );
                end              
            end
            always_ff @(posedge clk or posedge rst) begin
                if (rst) begin
                    data_in_valid_reg[STAGE] <= 1'b0;
                end else begin
                    data_in_valid_reg[STAGE] <= data_in_valid;
                end
            end
        end
    endgenerate

    // Output assignment
    assign data_out = data_reg[TRANSFORM_STAGES];

endmodule