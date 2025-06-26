`timescale 1ns / 1ps

/*
Module      : MXFP based Mini Systolic Array
Timing      : Sequential
Description : Since the data fed into the array is in diagonal format, the scale will always refer to the leftmost and topest element.
            : Then the shared scale will be passed along the systolic array.
            : In every PE, it need to take scale and minifloat as inputs.
Status      : Under Development
*/

module mxfp_mini_systolic_array #(
    // MX-FP Data Format
    parameter MXFP_T_EXP_WIDTH      = 4,
    parameter MXFP_T_MANT_WIDTH     = 3,
    parameter MXFP_L_EXP_WIDTH      = 4,
    parameter MXFP_L_MANT_WIDTH     = 3,
    parameter MXFP_SCALE_WIDTH      = 8,
    parameter BLOCK_DIM             = 4,

    // Accumulator Data Format
    parameter ACC_FP_EXP_WIDTH      = 8,
    parameter ACC_FP_MANT_WIDTH     = 7
)(

    input logic clk,
    input logic rst,

    // Input from Top
    input  logic [BLOCK_DIM - 1 : 0][MXFP_T_MANT_WIDTH + MXFP_T_EXP_WIDTH : 0] in_top_element,
    input  logic [MXFP_SCALE_WIDTH - 1 : 0] in_top_scale,
    input  logic system_top_valid,

    // Input from Left
    input  logic [BLOCK_DIM - 1 : 0][MXFP_L_MANT_WIDTH + MXFP_L_EXP_WIDTH : 0] in_left_element,
    input  logic [MXFP_SCALE_WIDTH - 1 : 0] in_left_scale,
    input  logic system_left_valid,

    // Mult Control
    input   logic mult_valid,
    output  logic mult_ready,

    // Output to Bottom
    output logic [BLOCK_DIM - 1 : 0][MXFP_T_MANT_WIDTH + MXFP_T_EXP_WIDTH : 0] out_bottom_element,
    output logic [MXFP_SCALE_WIDTH - 1 : 0] out_bottom_scale,

    // Output to Right
    output logic [BLOCK_DIM - 1 : 0][MXFP_L_MANT_WIDTH + MXFP_L_EXP_WIDTH : 0] out_right_element,
    output logic [MXFP_SCALE_WIDTH - 1 : 0] out_right_scale,

    // Output Result
    output logic [BLOCK_DIM - 1 : 0][BLOCK_DIM - 1 : 0][ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] out_fp,
    input  logic out_result_ready
);



logic [MXFP_T_EXP_WIDTH + MXFP_T_MANT_WIDTH : 0]  vert_transfer_elem     [BLOCK_DIM - 1:0][BLOCK_DIM :0];
logic [MXFP_SCALE_WIDTH - 1 : 0]                  vert_transfer_scale    [BLOCK_DIM : 0][BLOCK_DIM - 1:0];
logic [MXFP_L_EXP_WIDTH + MXFP_L_MANT_WIDTH : 0]  hori_transfer_elem        [BLOCK_DIM : 0][BLOCK_DIM - 1:0];
logic [MXFP_SCALE_WIDTH - 1 : 0]                  hori_transfer_scale       [BLOCK_DIM - 1:0][BLOCK_DIM :0];
logic [BLOCK_DIM - 1:0][BLOCK_DIM - 1:0] pe_compute_ready;

logic [BLOCK_DIM : 0][MXFP_SCALE_WIDTH - 1 : 0]  first_row_scale;
logic [BLOCK_DIM : 0][MXFP_SCALE_WIDTH - 1 : 0]  first_col_scale;

assign first_row_scale[0] = in_top_scale;
assign first_col_scale[0] = in_left_scale;

always_ff @(posedge clk) begin
    if (rst) begin
        first_col_scale <= 'b0;
        first_row_scale <= 'b0;
    end else begin
        for (int i = 0; i < BLOCK_DIM; i = i + 1) begin
            first_row_scale[i + 1] <= first_row_scale[i];
            first_col_scale[i + 1] <= first_col_scale[i];
        end
    end
end

generate;
    for (genvar i = 0; i < BLOCK_DIM; i = i + 1) begin : fill_with_input_data
        assign vert_transfer_elem[0][i]     = in_top_element[i];
        assign hori_transfer_elem[i][0]     = in_left_element[i];
        assign vert_transfer_scale[0][i]    = first_row_scale[i];
        assign hori_transfer_scale[i][0]    = first_col_scale[i];
    end
    assign mult_ready = &pe_compute_ready;
endgenerate


generate;
    for (genvar i = 0; i < BLOCK_DIM; i = i+1)begin : row_inx
        for (genvar j = 0; j < COMPUTE_DIM; j = j + 1) begin : col_idx
            mxfp_default_pe #(
                .MXFP_T_EXP_WIDTH   (MXFP_T_EXP_WIDTH),
                .MXFP_T_MANT_WIDTH  (MXFP_T_MANT_WIDTH),
                .MXFP_L_EXP_WIDTH   (MXFP_L_EXP_WIDTH),
                .MXFP_L_MANT_WIDTH  (MXFP_L_MANT_WIDTH),
                .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH),
                .ACC_FP_EXP_WIDTH   (ACC_FP_EXP_WIDTH),
                .ACC_FP_MANT_WIDTH  (ACC_FP_MANT_WIDTH)
            ) pe (
                .clk(clk),
                .rst(rst),
                .in_top_element         (vert_transfer_elem[i][j]),
                .in_top_scale           (vert_transfer_scale[i][j]),
                .system_top_valid       (system_top_valid),
                .in_left_element        (hori_transfer_elem[i][j]),
                .in_left_scale          (hori_transfer_scale[i][j]),
                .system_left_valid      (system_left_valid),
                .mult_valid             (mult_valid),
                .mult_ready             (pe_compute_ready[i][j]),
                .out_bottom_element     (vert_transfer_elem[i + 1][j]),
                .out_bottom_scale       (vert_transfer_scale[i + 1][j]),
                .out_right_element      (hori_transfer_elem[i][j + 1]),
                .out_right_scale        (hori_transfer_scale[i][j + 1]),
                .out_fp                 (out_fp[i][j]),
                .out_result_ready       (out_result_ready)
            );
        end
    end
endgenerate


generate;
    // Data Transfer Out from the mini systolic array.
    for (genvar i = 0; i < BLOCK_DIM; i = i + 1) begin : fill_output_data
        assign out_bottom_element[i] = vert_transfer_elem[i][BLOCK_DIM];
        assign out_right_element[i] = hori_transfer_elem[BLOCK_DIM][i];
    end
    assign out_bottom_scale   = vert_transfer_scale [BLOCK_DIM][0];
    assign out_right_scale    = hori_transfer_scale  [0][BLOCK_DIM];


    // Accumulated Result
    
endgenerate


endmodule