`timescale 1ns / 1ps

/*
Module      : MX-FP Configurable Precision Matrix Vector Multiplication Unit (With Sign)
Timing      : Sequential, Takes x cycles to compute the dot product
Description : Matrix Vector Multiplication with the same Tile
            : Assuming square matrix, this is the dimension of the matrix and the vector.
Status      : Under Development
*/

module mx_cp_mv #(
    // MX-FP Data Format
    parameter MXFP_EXP_WIDTH    = 4,
    parameter MXFP_MANT_WIDTH   = 3,
    parameter MXFP_SCALE_WIDTH  = 8,

    // Dimension
    parameter   COMPUTE_DIM          = 8, 
    parameter   BLOCK_DIM            = 4,
    localparam  BLOCK_NUM            = COMP_DIM / BLOCK_DIM,

    // Precision Control
    parameter   PRODUCT_EXT_EXP_WIDTH   = 1,
    parameter   PRODUCT_EXT_MANT_WIDTH  = 4,
    parameter   ADD_EXT_EXP_WIDTH       = 1,
    parameter   ADD_EXT_MANT_WIDTH      = 4,

    // Output Rounding Control
    parameter OUTPUT_ROUNDING = 1,
    parameter OUT_MAN_WIDTH = 3,
    parameter OUT_EXP_WIDTH = 4

) (
    input logic clk,
    input logic rst,

    // Input matrix
    input  logic [COMPUTE_DIM * COMPUTE_DIM - 1 : 0] [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] element_m_data,
    input  logic [BLOCK_NUM * BLOCK_NUM - 1 : 0] [MXFP_SCALE_WIDTH - 1 : 0] scale_m_data,
    input  logic               m_data_valid,
    output logic               m_data_ready,

    // Input vector
    input  logic [COMPUTE_DIM - 1 : 0] [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] element_v_data,
    input  logic [BLOCK_NUM - 1 : 0] [MXFP_SCALE_WIDTH - 1 : 0] scale_v_data,
    input  logic               v_data_valid,
    output logic               v_data_ready,

    // Output Vector
    output logic [COMPUTE_DIM - 1 : 0] [OUT_MAN_WIDTH + OUT_EXP_WIDTH : 0] element_out_data,
    output logic [BLOCK_NUM - 1 : 0] [MXFP_SCALE_WIDTH - 1 : 0] scale_out_data,
    output logic                 out_data_valid,
    input  logic                 out_data_ready
);

    localparam ACC_EXP_WIDTH  = IN_EXP_WIDTH + PRODUCT_EXT_EXP_WIDTH  + ADD_EXT_EXP_WIDTH * $clog2(BLOCK_DIM);
    localparam ACC_MANT_WIDTH = IN_MAN_WIDTH + PRODUCT_EXT_MANT_WIDTH + ADD_EXT_MANT_WIDTH * $clog2(BLOCK_DIM);

    initial begin
        if (OUTPUT_ROUNDING == 0) begin
        assert (ACC_EXP_WIDTH == OUT_EXP_WIDTH)
        else $fatal("OUT_EXP_WIDTH must be %d if OUTPUT_ROUNDING == 0", ACC_EXP_WIDTH);
        assert (ACC_MANT_WIDTH == OUT_MAN_WIDTH)
        else $fatal("OUT_MAN_WIDTH must be %d if OUTPUT_ROUNDING == 0", ACC_MANT_WIDTH);
        end
    end


    // -----
    // Wires
    // -----

    logic dot_product_ready;
    logic inputs_valid, inputs_ready;

    logic [COMPUTE_DIM-1:0] dot_product_valid;
    logic [COMPUTE_DIM-1:0] sync_ready;

    logic [COMPUTE_DIM - 1 : 0][ACC_EXP_WIDTH + ACC_MANT_WIDTH:0] element_prod_out;
    logic [COMPUTE_DIM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0] scale_prod_out;

//   logic [COMPUTE_DIM - 1 : 0][OUT_EXP_WIDTH + OUT_MAN_WIDTH:0]  rounded_dot_product;


    // -----
    // Logic
    // -----

    // Need to synchronise x & y inputs
    assign inputs_ready = sync_ready[0];
    join2 sync_handshake (
        .data_in_valid ({m_data_valid, v_data_valid}),
        .data_in_ready ({m_data_ready, v_data_ready}),
        .data_out_valid(inputs_valid),
        .data_out_ready(inputs_ready)
    );

    generate;
        // Instantiate COMPUTE_DIM number of dot products
        for (genvar i = 0; i < COMPUTE_DIM; i++) begin : row_matrix_by_vec
            mx_fp_dot_product #(
                .MXFP_EXP_WIDTH    (MXFP_EXP_WIDTH),
                .MXFP_MANT_WIDTH   (MXFP_MANT_WIDTH),
                .MXFP_SCALE_WIDTH  (MXFP_SCALE_WIDTH),
                .COMP_DIM          (COMPUTE_DIM),
                .BLOCK_DIM         (BLOCK_DIM),
                .PRODUCT_EXT_EXP_WIDTH   (PRODUCT_EXT_EXP_WIDTH),
                .PRODUCT_EXT_MANT_WIDTH  (PRODUCT_EXT_MANT_WIDTH),
                .ADD_EXT_EXP_WIDTH       (ADD_EXT_EXP_WIDTH),
                .ADD_EXT_MANT_WIDTH      (ADD_EXT_MANT_WIDTH)
            ) dot_product_inst (
                .clk                  (clk),
                .rst                  (rst),
                .element_a_in         (element_m_data[((i+1)*COMPUTE_DIM)-1 : i*COMPUTE_DIM]),
                .scale_a_in           (scale_m_data[((i+1)*BLOCK_NUM)-1 : i*BLOCK_NUM]),
                .data_a_in_valid      (inputs_valid),
                .data_a_in_ready      (sync_ready[i]),
                .element_b_in         (element_v_data),
                .scale_b_in           (scale_v_data),
                .data_b_in_valid      (inputs_valid),
                .data_b_in_ready      (), // same as data_a_in_ready
                .element_out          (element_prod_out[i]),
                .scale_out            (scale_prod_out[i]),
                .data_out_valid       (dot_product_valid[i]),
                .data_out_ready       (dot_product_ready)
            );
        end
    endgenerate

    assign out_data_valid = dot_product_valid[0];
    assign dot_product_ready = out_data_ready;

        
    generate;
        for (genvar j = 0; j < BLOCK_NUM; j++) begin
            mx_fp_rescale #(
                .INPUT_EXP_WIDTH(ACC_EXP_WIDTH),
                .INPUT_MANT_WIDTH(ACC_MANT_WIDTH),
                .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
                .BLOCK_DIM(BLOCK_DIM),
                .MXFP_EXP_WIDTH(MX_FP_EXP_WIDTH),
                .MXFP_MANT_WIDTH(MX_FP_MANT_WIDTH)
            ) (
                .clk(clk),
                .rst(rst),
                .element_in(element_prod_out[j]),
                .scale_in(scale_prod_out[j]),
                .element_data_out(element_out_data[j]),
                .scale_data_out(scale_out_data[j])
            )

        end
    endgenerate

endmodule
