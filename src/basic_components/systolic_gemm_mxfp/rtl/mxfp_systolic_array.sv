`timescale 1ns / 1ps

/*
Module      : Systolic Array
Timing      : Sequential
Description : It can be used for both GEMM and GEMV operations.
Status      : Under Development
*/

module systolic_array #(
    // MX-FP Data Format
    parameter MXFP_EXP_WIDTH        = 4,
    parameter MXFP_MANT_WIDTH       = 3,
    parameter MXFP_SCALE_WIDTH      = 8,
    parameter BLOCK_DIM             = 4,
    // Accumulator Data Format
    parameter ACC_FP_EXP_WIDTH      = 8,
    parameter ACC_FP_MANT_WIDTH     = 7,
    // Dimension
    parameter COMPUTE_DIM           = 8,
    localparam BLOCK_NUM            = COMPUTE_DIM / BLOCK_DIM
)(

    input   logic clk,
    input   logic rst,
    input   logic control,

    // Input from Top Array
    input   logic [COMPUTE_DIM - 1: 0] [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] in_top_element,
    input   logic [BLOCK_NUM - 1: 0] [MXFP_SCALE_WIDTH - 1 : 0] in_top_scale,
    input   logic in_top_valid,
    output  logic in_top_ready,

    // Input from Left Array
    input   logic [COMPUTE_DIM - 1: 0] [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] in_left_element,
    input   logic [BLOCK_NUM - 1: 0] [MXFP_SCALE_WIDTH - 1 : 0] in_left_scale,
    input   logic in_left_valid,
    output  logic in_left_ready,

    // Input from Vector Array
    input   logic [COMPUTE_DIM - 1: 0] [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] in_top_v_element,
    input   logic [BLOCK_NUM - 1: 0] [MXFP_SCALE_WIDTH - 1 : 0] in_top_v_scale,
    input   logic in_top_v_valid,
    output  logic in_top_v_ready,

    // Output GEMM
    output  logic [COMPUTE_DIM- 1: 0] [COMPUTE_DIM - 1: 0] [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] m_out_fp,
    output  logic m_out_valid,
    input   logic m_out_ready,

    // Output GEMV
    output  logic [COMPUTE_DIM - 1: 0] [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] v_out_fp,
    output  logic v_out_valid,
    input   logic v_out_ready
    
);


    initial begin
        if (COMPUTE_DIM % BLOCK_DIM != 0) begin
            $error("COMPUTE_DIM must be a multiple of BLOCK_DIM");
            $finish;
        end
    end

    logic [COMPUTE_DIM - 1:0] distributed_in_top_valid;
    logic [COMPUTE_DIM - 1:0] distributed_in_top_ready;
    logic [COMPUTE_DIM - 1:0] distributed_in_left_valid;
    logic [COMPUTE_DIM - 1:0] distributed_in_left_ready;
    logic [COMPUTE_DIM - 1:0] distributed_in_top_v_valid;
    logic [COMPUTE_DIM - 1:0] distributed_in_top_v_ready;

    split_n #(
        .N(COMPUTE_DIM)
    ) split_top (
        .data_in_valid(in_top_valid),
        .data_in_ready(in_top_ready),
        .data_out_valid(distributed_in_top_valid),
        .data_out_ready(distributed_in_top_ready)
    );

    split_n #(
        .N(COMPUTE_DIM)
    ) split_left (
        .data_in_valid(in_left_valid),
        .data_in_ready(in_left_ready),
        .data_out_valid(distributed_in_left_valid),
        .data_out_ready(distributed_in_left_ready)
    );

    split_n #(
        .N(COMPUTE_DIM)
    ) split_top_v (
        .data_in_valid(in_top_v_valid),
        .data_in_ready(in_top_v_ready),
        .data_out_valid(distributed_in_top_v_valid),
        .data_out_ready(distributed_in_top_v_ready)
    );

    logic rowwise_data_transfer_valid [COMPUTE_DIM - 1:0][COMPUTE_DIM :0];
    logic rowwise_data_transfer_ready [COMPUTE_DIM - 1:0][COMPUTE_DIM :0];
    logic [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0]    rowwise_data_transfer_element   [COMPUTE_DIM - 1:0][COMPUTE_DIM :0];
    logic [MXFP_SCALE_WIDTH - 1 : 0]                rowwise_data_transfer_scale     [COMPUTE_DIM - 1:0][COMPUTE_DIM :0];

    logic columnwise_data_transfer_valid [COMPUTE_DIM :0][COMPUTE_DIM - 1:0];
    logic columnwise_data_transfer_ready [COMPUTE_DIM :0][COMPUTE_DIM - 1:0];
    logic [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0]    columnwise_data_transfer_element    [COMPUTE_DIM : 0][COMPUTE_DIM - 1:0];
    logic [MXFP_SCALE_WIDTH - 1 : 0]                columnwise_data_transfer_scale      [COMPUTE_DIM : 0][COMPUTE_DIM - 1:0];

    logic [COMPUTE_DIM- 1: 0] [COMPUTE_DIM - 1: 0] [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] result_values;
    logic [COMPUTE_DIM- 1: 0] [COMPUTE_DIM - 1: 0] result_valid;
    logic [COMPUTE_DIM- 1: 0] [COMPUTE_DIM - 1: 0] result_ready;

    // Fill the Front Top Row and Left Column with the input data
    generate;
        for (genvar i = 0; i < COMPUTE_DIM; i = i + 1) begin : fill_with_input_data
            // Fill the Top Row
            assign columnwise_data_transfer_element[0][i]  = in_top_element[i];
            assign columnwise_data_transfer_scale  [0][i]  = in_top_scale[i / BLOCK_DIM];
            assign columnwise_data_transfer_valid[0][i]    = distributed_in_top_valid[i];
            assign distributed_in_top_ready[i]          = columnwise_data_transfer_ready[0][i];

            // Fill the Left Column
            assign rowwise_data_transfer_element[i][0]   = in_left_element[i];
            assign rowwise_data_transfer_scale  [i][0]   = in_left_scale[i / BLOCK_DIM];
            assign rowwise_data_transfer_valid[i][0]     = distributed_in_left_valid[i];
            assign distributed_in_left_ready[i]          = rowwise_data_transfer_ready[i][0];
        end
    endgenerate

    // Fill the Bottom and Left Most Data Extraction Signals
    generate;
        for (genvar i = 0; i < COMPUTE_DIM; i = i + 1) begin : fill_extraction_signals
            assign rowwise_data_transfer_ready[i][COMPUTE_DIM]      = 1'b1;
            assign columnwise_data_transfer_ready[COMPUTE_DIM][i]   = 1'b1;
        end
    endgenerate


    // Computation
    generate;
        for (genvar i = 0; i < COMPUTE_DIM; i = i + 1) begin : pe_row
            for (genvar j = 0; j < COMPUTE_DIM; j = j + 1) begin : pe_col
                if (i == 0) begin
                    first_row_pe #(
                        .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
                        .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
                        .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
                        .ACC_FP_EXP_WIDTH(ACC_FP_EXP_WIDTH),
                        .ACC_FP_MANT_WIDTH(ACC_FP_MANT_WIDTH)
                    ) first_row_pe_init (
                        .clk(clk),
                        .rst(rst),
                        .control(control),

                        // Input from Top Array
                        .in_top_element (columnwise_data_transfer_element[i][j]),
                        .in_top_scale   (columnwise_data_transfer_scale[i][j]),
                        .in_top_valid   (columnwise_data_transfer_valid[i][j]),
                        .in_top_ready   (columnwise_data_transfer_ready[i][j]),

                        // Input from Left Array
                        .in_left_element(rowwise_data_transfer_element[i][j]),
                        .in_left_scale  (rowwise_data_transfer_scale[i][j]),
                        .in_left_valid  (rowwise_data_transfer_valid[i][j]),
                        .in_left_ready  (rowwise_data_transfer_ready[i][j]),

                        // Input from Vector Array
                        .in_top_v_element   (in_top_v_element[j]),
                        .in_top_v_scale     (in_top_v_scale[j]),
                        .in_top_v_valid     (distributed_in_top_v_valid[j]),
                        .in_top_v_ready     (distributed_in_top_v_ready[j]),

                        // Output to Bottom
                        .out_bottom_element (columnwise_data_transfer_element[i+1][j]),
                        .out_bottom_scale   (columnwise_data_transfer_scale[i+1][j]),
                        .out_bottom_valid   (columnwise_data_transfer_valid[i+1][j]),
                        .out_bottom_ready   (columnwise_data_transfer_ready[i+1][j]),

                        // Output to Right
                        .out_right_element  (rowwise_data_transfer_element[i][j+1]),
                        .out_right_scale    (rowwise_data_transfer_scale[i][j+1]),
                        .out_right_valid    (rowwise_data_transfer_valid[i][j+1]),
                        .out_right_ready    (rowwise_data_transfer_ready[i][j+1]),

                        // Output Result
                        .out_fp             (m_out_fp[i][j]),
                        .out_result_valid   (result_valid[i][j]),
                        .out_result_ready   (result_ready[i][j])
                    );
                end else begin
                    default_pe #(
                        .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
                        .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
                        .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
                        .ACC_FP_EXP_WIDTH(ACC_FP_EXP_WIDTH),
                        .ACC_FP_MANT_WIDTH(ACC_FP_MANT_WIDTH)
                    ) default_pe_init (
                        .clk(clk),
                        .rst(rst),

                        // Input from Top Array
                        .in_top_element (columnwise_data_transfer_element[i][j]),
                        .in_top_scale   (columnwise_data_transfer_scale[i][j]),
                        .in_top_valid   (columnwise_data_transfer_valid[i][j]),
                        .in_top_ready   (columnwise_data_transfer_ready[i][j]),

                        // Input from Left Array
                        .in_left_element(rowwise_data_transfer_element[i][j]),
                        .in_left_scale  (rowwise_data_transfer_scale[i][j]),
                        .in_left_valid  (rowwise_data_transfer_valid[i][j]),
                        .in_left_ready  (rowwise_data_transfer_ready[i][j]),

                        // Output to Bottom
                        .out_bottom_element (columnwise_data_transfer_element[i + 1][j]),
                        .out_bottom_scale   (columnwise_data_transfer_scale[i + 1][j]),
                        .out_bottom_valid   (columnwise_data_transfer_valid[i + 1][j]),
                        .out_bottom_ready   (columnwise_data_transfer_ready[i + 1][j]),

                        // Output to Right
                        .out_right_element  (rowwise_data_transfer_element[i][j + 1]),
                        .out_right_scale    (rowwise_data_transfer_scale[i][j + 1]),
                        .out_right_valid    (rowwise_data_transfer_valid[i][j + 1]),
                        .out_right_ready    (rowwise_data_transfer_ready[i][j + 1]),

                        // Output Result
                        .out_fp             (m_out_fp[i][j]),
                        .out_result_valid   (result_valid[i][j]),
                        .out_result_ready   (result_ready[i][j])
                    );
                end
            end
        end
    endgenerate

    assign out_result_valid = & result_valid;
    assign result_ready     = (out_result_ready) ? {(COMPUTE_DIM * COMPUTE_DIM){1'b1}} : result_ready;
    assign m_out_valid      = out_result_valid;
    assign v_out_valid      = out_result_valid;
    assign v_out_fp         = m_out_fp[0];
    assign out_result_ready = control ? m_out_ready : v_out_ready;

endmodule