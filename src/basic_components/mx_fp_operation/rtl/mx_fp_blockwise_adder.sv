`timescale 1ns / 1ps

/*
Module      : MX-FP Configurable Precision Blockwise Adder
Description : 
Timing      : 2 shifts
Input   e1  |       e1  |
        e2  | s1 +  e2  | s2
        e3  |       e3  |
        e4  |       e4  |
Status      : Under Testing
*/

module mx_fp_blockwise_adder #(
    // MX-FP Data Format
    parameter MXFP_EXP_WIDTH = 4,
    parameter MXFP_MANT_WIDTH = 3,
    parameter MXFP_SCALE_WIDTH = 8,
    
    // Precision Control
    parameter EXT_MANT_WIDTH = 1,
    parameter EXT_EXP_WIDTH = 1,

    // Dimension
    parameter BLOCK_DIM = 4
) (
    input  logic                 clk,
    input  logic                 rst,
    // Port A
    input  logic [BLOCK_DIM-1:0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]  a_element_data_in,
    input  logic [MXFP_SCALE_WIDTH - 1 : 0]                             a_scale_data_in,
    input  logic                                                        a_data_in_valid,
    output logic                                                        a_data_in_ready,
    // Port B
    input  logic [BLOCK_DIM-1:0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]  b_element_data_in,
    input  logic [MXFP_SCALE_WIDTH - 1 : 0]                             b_scale_data_in,
    input  logic                                                        b_data_in_valid,
    output logic                                                        b_data_in_ready,
    // Output
    output logic [BLOCK_DIM-1:0][MXFP_EXP_WIDTH + EXT_EXP_WIDTH + MXFP_MANT_WIDTH + EXT_MANT_WIDTH : 0]  element_data_out,
    output logic [MXFP_SCALE_WIDTH - 1 : 0]                             scale_data_out,
    output logic                                                        data_out_valid,
    input  logic                                                        data_out_ready
);

    logic [MXFP_SCALE_WIDTH - 1 : 0]                             max_scale_data_in, p1_max_scale_data_in, p2_max_scale_data_in, p3_max_scale_data_in;

    logic [MXFP_SCALE_WIDTH - 1 : 0] shift_amount;
    logic [BLOCK_DIM-1:0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] elements_to_shift;

    logic [BLOCK_DIM-1:0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] elements_wo_shift;
    logic [BLOCK_DIM-1:0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] elements_stored_wo_shift;

    logic [BLOCK_DIM-1:0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] elements_ready_shift;
    logic [BLOCK_DIM-1:0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] elements_af_shift;
    logic [BLOCK_DIM-1:0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] elements_stored_shift;

    logic wo_shift_in_valid, wo_shift_in_ready;
    logic wo_shift_out_ready, wo_shift_out_valid;
    logic to_shift_in_valid, to_shift_in_ready;
    logic to_shift_out_ready, to_shift_out_valid;
    logic af_shift_out_ready, af_shift_out_valid;
    logic af_shift_in_valid, af_shift_in_ready;

    always_comb begin
        if (a_scale_data_in > b_scale_data_in) begin : gen_a_greater
            shift_amount = a_scale_data_in - b_scale_data_in;
            elements_ready_shift = b_element_data_in;
            elements_wo_shift = a_element_data_in;
            max_scale_data_in = a_scale_data_in;
            wo_shift_in_valid = a_data_in_valid;
            to_shift_in_valid = b_data_in_valid;
            a_data_in_ready = wo_shift_in_ready;
            b_data_in_ready = to_shift_in_ready;

        end else begin : gen_b_greater
            shift_amount = b_scale_data_in - a_scale_data_in;
            elements_ready_shift = a_element_data_in;
            elements_wo_shift = b_element_data_in;
            max_scale_data_in = b_scale_data_in;
            wo_shift_in_valid = b_data_in_valid;
            to_shift_in_valid = a_data_in_valid;
            a_data_in_ready = to_shift_in_ready;
            b_data_in_ready = wo_shift_in_ready;
        end
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            p1_max_scale_data_in <= 0;
            p2_max_scale_data_in <= 0;
            p3_max_scale_data_in <= 0;
        end else begin
            p1_max_scale_data_in <= max_scale_data_in;
            p2_max_scale_data_in <= p1_max_scale_data_in;
            p3_max_scale_data_in <= p2_max_scale_data_in;
        end
    end

    assign scale_data_out = p3_max_scale_data_in;

    // Shift the elements
    generate
        
        skid_buffer #(
            .DATA_WIDTH(BLOCK_DIM * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1))
        ) store_data_to_shift_element (
            .clk(clk),
            .rst(rst),
            .data_in        (elements_ready_shift),
            .data_in_valid  (to_shift_in_valid),
            .data_in_ready  (to_shift_in_ready),
            .data_out       (elements_to_shift),
            .data_out_valid (to_shift_out_valid),
            .data_out_ready (to_shift_out_ready)
        );

        skid_buffer #(
            .DATA_WIDTH(BLOCK_DIM * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1))
        ) store_wo_shifted_element (
            .clk(clk),
            .rst(rst),
            .data_in        (elements_wo_shift),
            .data_in_valid  (wo_shift_in_valid),
            .data_in_ready  (wo_shift_in_ready),
            .data_out       (elements_stored_wo_shift),
            .data_out_valid (wo_shift_out_valid),
            .data_out_ready (wo_shift_out_ready)
        );
        
        for(genvar i = 0; i < BLOCK_DIM; i++) begin : gen_block_shift
            fp_shift #(
                .EXP_WIDTH(MXFP_EXP_WIDTH),
                .MANT_WIDTH(MXFP_MANT_WIDTH)
            ) mx_fp_shift (
                .data_in        (elements_to_shift[i]),
                .shift_amount   (shift_amount),
                .data_out       (elements_af_shift[i])
            );
        end

        assign af_shift_in_valid = to_shift_out_valid;
        assign to_shift_out_ready = af_shift_in_ready;
        
        skid_buffer #(
            .DATA_WIDTH(BLOCK_DIM * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1))
        ) store_shifted_element (
            .clk(clk),
            .rst(rst),
            .data_in            (elements_af_shift),
            .data_in_valid      (af_shift_in_valid),
            .data_in_ready      (af_shift_in_ready),
            .data_out           (elements_stored_shift),
            .data_out_valid     (af_shift_out_valid),
            .data_out_ready     (af_shift_out_ready)
        );

    endgenerate


    logic addition_in_valid, addition_in_ready;
    logic [BLOCK_DIM-1:0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] element_addition_result;
    // FP Addition, TODO: how to consider the overflow problem, whether to add to the mx-fp scale?
    generate;
        for(genvar i = 0; i < BLOCK_DIM; i++) begin : gen_block_adder
            fp_cp_adder_v2 #(
                .EXP_WIDTH(MXFP_EXP_WIDTH),
                .MANT_WIDTH(MXFP_MANT_WIDTH),
                .EXT_EXP_WIDTH(EXT_EXP_WIDTH),
                .EXT_MANT_WIDTH(EXT_MANT_WIDTH)
            ) fp_adder (
                .data_a     (elements_stored_wo_shift[i]),
                .data_b     (elements_stored_shift[i]),
                .data_out   (element_addition_result[i])
            );
        end

        join2 #() join_inst (
            .data_in_ready ({wo_shift_out_ready, af_shift_out_ready}),
            .data_in_valid ({wo_shift_out_valid, af_shift_out_valid}),
            .data_out_valid(addition_in_valid),
            .data_out_ready(addition_in_ready)
        );

        skid_buffer #(
            .DATA_WIDTH(BLOCK_DIM * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1))
        ) store_addition_result (
            .clk(clk),
            .rst(rst),
            .data_in(element_addition_result),
            .data_in_valid(addition_in_valid),
            .data_in_ready(addition_in_ready),
            .data_out(element_data_out),
            .data_out_valid(data_out_valid),
            .data_out_ready(data_out_ready)
        );
    endgenerate


endmodule