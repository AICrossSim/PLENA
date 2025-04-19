`timescale 1ns / 1ps

/*
Module      : MX-FP Configurable Precision Matrix Vector Multiplication Unit (With Sign)
Timing      : Sequential, Takes x cycles to compute the dot product
Description : Matrix Vector Multiplication with the same Tile
            : Assuming square matrix, this is the dimension of the matrix and the vector.
Status      : Pass Simple Test
*/

module mx_fp_mv #(
    // MX-FP Data Format
    parameter MXFP_EXP_WIDTH    = 4,
    parameter MXFP_MANT_WIDTH   = 3,
    parameter MXFP_SCALE_WIDTH  = 8,

    // Dimension
    parameter   COMPUTE_DIM          = 8, 
    parameter   BLOCK_DIM            = 4,
    localparam  BLOCK_NUM            = COMPUTE_DIM / BLOCK_DIM,

    // Precision Control
    parameter   PRODUCT_EXT_EXP_WIDTH   = 1,
    parameter   PRODUCT_EXT_MANT_WIDTH  = 0,
    parameter   BLOCK_ADD_EXT_EXP_WIDTH       = 1,
    parameter   BLOCK_ADD_EXT_MANT_WIDTH      = 0,
    parameter   FP_ADD_EXT_EXP_WIDTH       = 1,
    parameter   FP_ADD_EXT_MANT_WIDTH      = 0,

    // Output Rounding Control
    parameter   OUTPUT_FP_ROUND_EN      = 0,
    parameter   ROUND_FP_EXP_WIDTH     = 4,
    parameter   ROUND_FP_MANT_WIDTH    = 3

) (
    input logic clk,
    input logic rst,

    // Input matrix
    input  logic [COMPUTE_DIM * COMPUTE_DIM - 1 : 0]    [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] m_element,
    input  logic [BLOCK_NUM   * COMPUTE_DIM - 1 : 0]        [MXFP_SCALE_WIDTH - 1 : 0] m_scale,
    input  logic               m_valid,
    output logic               m_ready,

    // Input vector
    input  logic [COMPUTE_DIM - 1 : 0]  [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] v_element,
    input  logic [BLOCK_NUM - 1 : 0]    [MXFP_SCALE_WIDTH - 1 : 0] v_scale,
    input  logic               v_valid,
    output logic               v_ready,

    // Output Vector: Same Dimension as the Input Vector
    output logic [COMPUTE_DIM - 1 : 0]  [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] out_element,
    output logic [BLOCK_NUM - 1 : 0]    [MXFP_SCALE_WIDTH - 1 : 0] out_scale,
    output logic                 out_valid,
    input  logic                 out_ready
);

    localparam ACC_EXP_WIDTH  = (OUTPUT_FP_ROUND_EN == 1) ? ROUND_FP_EXP_WIDTH  : MXFP_EXP_WIDTH + PRODUCT_EXT_EXP_WIDTH  + BLOCK_ADD_EXT_EXP_WIDTH  * $clog2(BLOCK_DIM) + FP_ADD_EXT_EXP_WIDTH  * $clog2(BLOCK_NUM);
    localparam ACC_MANT_WIDTH = (OUTPUT_FP_ROUND_EN == 1) ? ROUND_FP_MANT_WIDTH : MXFP_MANT_WIDTH + PRODUCT_EXT_MANT_WIDTH + BLOCK_ADD_EXT_MANT_WIDTH * $clog2(BLOCK_DIM) + FP_ADD_EXT_MANT_WIDTH * $clog2(BLOCK_NUM);

    initial begin
        if (OUTPUT_FP_ROUND_EN == 1) begin  // TODO
            assert (ACC_EXP_WIDTH == ROUND_FP_EXP_WIDTH)
            else $fatal("OUT_EXP_WIDTH must be %d if OUTPUT_ROUNDING == 0", ACC_EXP_WIDTH);
            assert (ACC_MANT_WIDTH == ROUND_FP_MANT_WIDTH)
            else $fatal("OUT_MAN_WIDTH must be %d if OUTPUT_ROUNDING == 0", ACC_MANT_WIDTH);
        end
    end


    // -----
    // Wires
    // -----

    logic [BLOCK_NUM -1 : 0] convert_in_ready;
    logic dot_prod_out_ready;
    logic inputs_valid, inputs_ready;

    logic [COMPUTE_DIM-1:0] dot_product_valid;
    logic [COMPUTE_DIM-1:0] sync_ready;

    logic [COMPUTE_DIM - 1 : 0][ACC_EXP_WIDTH + ACC_MANT_WIDTH:0] fp_dot_out;

    // -----
    // Logic
    // -----

    // Need to synchronise x & y inputs
    assign inputs_ready = sync_ready[0];
    join2 sync_handshake (
        .data_in_valid ({m_valid, v_valid}),
        .data_in_ready ({m_ready, v_ready}),
        .data_out_valid(inputs_valid),
        .data_out_ready(inputs_ready)
    );

    generate;
        // Instantiate COMPUTE_DIM number of dot products
        for (genvar i = 0; i < COMPUTE_DIM; i++) begin : row_matrix_by_vec
            mx_fp_dot_product_fp_out #(
                .MXFP_EXP_WIDTH    (MXFP_EXP_WIDTH),
                .MXFP_MANT_WIDTH   (MXFP_MANT_WIDTH),
                .MXFP_SCALE_WIDTH  (MXFP_SCALE_WIDTH),
                .COMP_DIM          (COMPUTE_DIM),
                .BLOCK_DIM         (BLOCK_DIM),
                .PRODUCT_EXT_EXP_WIDTH          (PRODUCT_EXT_EXP_WIDTH),
                .PRODUCT_EXT_MANT_WIDTH         (PRODUCT_EXT_MANT_WIDTH),
                .BLOCK_ADD_EXT_EXP_WIDTH        (BLOCK_ADD_EXT_EXP_WIDTH),
                .BLOCK_ADD_EXT_MANT_WIDTH       (BLOCK_ADD_EXT_MANT_WIDTH),
                .FP_ADD_EXT_EXP_WIDTH           (FP_ADD_EXT_EXP_WIDTH),
                .FP_ADD_EXT_MANT_WIDTH          (FP_ADD_EXT_MANT_WIDTH),
                .OUTPUT_FP_ROUND_EN             (OUTPUT_FP_ROUND_EN),
                .ROUND_FP_EXP_WIDTH             (ROUND_FP_EXP_WIDTH),
                .ROUND_FP_MANT_WIDTH            (ROUND_FP_MANT_WIDTH)
            ) dot_product_inst (
                .clk                  (clk),
                .rst                  (rst),
                .element_a_in         (m_element[((i+1)*COMPUTE_DIM)-1 : i*COMPUTE_DIM]),
                .scale_a_in           (m_scale[((i+1)*BLOCK_NUM)-1 : i*BLOCK_NUM]),
                .data_a_in_valid      (inputs_valid),
                .data_a_in_ready      (sync_ready[i]),
                .element_b_in         (v_element),
                .scale_b_in           (v_scale),
                .data_b_in_valid      (inputs_valid),
                .data_b_in_ready      (), // same as data_a_in_ready
                .data_out             (fp_dot_out[i]),
                .data_out_valid       (dot_product_valid[i]),
                .data_out_ready       (dot_prod_out_ready)
            );
        end
        assign dot_prod_out_ready = &convert_in_ready;
    endgenerate
        
    generate;

        for (genvar j = 0; j < BLOCK_NUM; j++) begin
            fp_2_mx_fp_block #(
                .BLOCK_DIM(BLOCK_DIM),
                .FP_MANT_WIDTH(ACC_MANT_WIDTH),
                .FP_EXP_WIDTH(ACC_EXP_WIDTH),
                .MX_FP_MANT_WIDTH(MXFP_MANT_WIDTH),
                .MX_FP_EXP_WIDTH(MXFP_EXP_WIDTH),
                .MX_FP_SCALE_WIDTH(MXFP_SCALE_WIDTH)
            ) fp_2_mx_convert(
                .clk(clk),
                .rst(rst),
                .data_in(fp_dot_out[(j+1)*BLOCK_DIM-1 : j*BLOCK_DIM]),
                .data_in_valid(dot_product_valid[0]),
                .data_in_ready(convert_in_ready[i]),
                .element_data_out(out_element[(j+1)*BLOCK_DIM-1 : j*BLOCK_DIM]),
                .scale_data_out(out_scale[j]),
                .mx_fp_data_out_valid(out_valid),
                .mx_fp_data_out_ready(out_ready)
            );

        end
    endgenerate

endmodule
