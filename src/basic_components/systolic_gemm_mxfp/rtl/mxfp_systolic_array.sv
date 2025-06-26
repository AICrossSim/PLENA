`timescale 1ns / 1ps

/*
Module      : MXFP Systolic Array
Timing      : Sequential
Description : It can be used for both GEMM and GEMV operations.
Status      : Under Development
*/

module mxfp_systolic_array #(
    // MX-FP Data Format
    parameter MXFP_T_EXP_WIDTH      = 4,
    parameter MXFP_T_MANT_WIDTH     = 3,
    parameter MXFP_L_EXP_WIDTH      = 4,
    parameter MXFP_L_MANT_WIDTH     = 3,
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
    input   logic [BLOCK_NUM - 1: 0]    [BLOCK_DIM * (MXFP_T_MANT_WIDTH + MXFP_T_EXP_WIDTH + 1) - 1 : 0] in_top_element,
    input   logic [BLOCK_NUM - 1: 0]    [MXFP_SCALE_WIDTH - 1 : 0] in_top_scale,
    input   logic in_top_valid,
    output  logic in_top_ready,

    // Input from Left Array
    input   logic [COMPUTE_DIM - 1: 0]  [BLOCK_DIM * (MXFP_L_MANT_WIDTH + MXFP_L_EXP_WIDTH + 1) - 1 : 0] in_left_element,
    input   logic [BLOCK_NUM - 1: 0]    [MXFP_SCALE_WIDTH - 1 : 0] in_left_scale,
    input   logic in_left_valid,
    output  logic in_left_ready,

    // Input from Vector Array
    input   logic [BLOCK_NUM - 1: 0]    [BLOCK_DIM * (MXFP_L_MANT_WIDTH + MXFP_L_EXP_WIDTH + 1) - 1 : 0] in_left_v_element,
    input   logic [BLOCK_NUM - 1: 0]    [MXFP_SCALE_WIDTH - 1 : 0] in_left_v_scale,
    input   logic in_top_v_valid,
    output  logic in_top_v_ready,

    // Output GEMM
    output  logic [COMPUTE_DIM - 1: 0]  [COMPUTE_DIM - 1: 0] [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] m_out_fp,
    input   logic m_out_ready,

    // Output GEMV
    output  logic [COMPUTE_DIM - 1: 0]  [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] v_out_fp,
    input   logic v_out_ready
    
);

    initial begin
        if (COMPUTE_DIM % BLOCK_DIM != 0) begin
            $error("COMPUTE_DIM must be a multiple of BLOCK_DIM");
            $finish;
        end
    end


    logic [BLOCK_DIM * ( MXFP_T_MANT_WIDTH + MXFP_T_EXP_WIDTH + 1 ) - 1 : 0]    vert_transfer_elem      [BLOCK_NUM - 1:0][BLOCK_NUM :0];
    logic [MXFP_SCALE_WIDTH - 1 : 0]                                            vert_transfer_scale     [BLOCK_NUM - 1:0][BLOCK_NUM :0];

    logic [BLOCK_DIM * ( MXFP_L_MANT_WIDTH + MXFP_L_EXP_WIDTH + 1 ) - 1 : 0]    hori_transfer_elem      [BLOCK_NUM : 0][BLOCK_NUM - 1:0];
    logic [MXFP_SCALE_WIDTH - 1 : 0]                                            hori_transfer_scale     [BLOCK_NUM : 0][BLOCK_NUM - 1:0];

    logic [BLOCK_NUM- 1: 0][BLOCK_NUM- 1: 0][BLOCK_DIM - 1: 0][[BLOCK_DIM - 1: 0]][ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] result_values;
    logic [BLOCK_NUM- 1: 0] [BLOCK_NUM - 1: 0] result_valid;
    logic [BLOCK_NUM- 1: 0] [BLOCK_NUM - 1: 0] result_ready;

    logic mult_valid, mult_ready;
    logic system_right_shift_valid, system_down_shift_valid;
    logic [BLOCK_NUM- 1: 0] [BLOCK_NUM - 1: 0] pe_compute_ready;


    generate;
        for (genvar i = 0; i < BLOCK_NUM; i = i + 1) begin : fill_with_input_data
            // Fill the Top Row
            assign hori_transfer_elem[0][i]      = in_top_element[i];
            assign hori_transfer_scale[0][i]     = in_top_scale[i];

            // Fill the Left Column
            assign vert_transfer_elem[i][0]      = in_left_element[i];
            assign vert_transfer_scale[i][0]     = in_left_scale[i];
        end
    endgenerate



    // Computation
    generate;
        for (genvar i = 0; i < BLOCK_NUM; i = i + 1) begin : pe_row
            for (genvar j = 0; j < BLOCK_NUM; j = j + 1) begin : pe_col
                if (i == 0) begin
                    mxfp_first_row_mini_systolic_array #(
                        .MXFP_T_EXP_WIDTH   (MXFP_T_EXP_WIDTH),
                        .MXFP_T_MANT_WIDTH  (MXFP_T_MANT_WIDTH),
                        .MXFP_L_EXP_WIDTH   (MXFP_L_EXP_WIDTH),
                        .MXFP_L_MANT_WIDTH  (MXFP_L_MANT_WIDTH),
                        .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH),
                        .BLOCK_DIM          (BLOCK_DIM),
                        .ACC_FP_EXP_WIDTH   (ACC_FP_EXP_WIDTH),
                        .ACC_FP_MANT_WIDTH  (ACC_FP_MANT_WIDTH)
                    ) first_row_pe_init (
                        .clk(clk),
                        .rst(rst),
                        .control(control),

                        // Input from Top Array
                        .in_top_element (hori_transfer_elem[i][j]),
                        .in_top_scale   (hori_transfer_scale[i][j]),

                        // Input from Left Array
                        .in_left_element(vert_transfer_elem[i][j]),
                        .in_left_scale  (vert_transfer_scale[i][j]),

                        // Input from Vector Array
                        .in_left_v_element   (in_left_v_element[j]),
                        .in_left_v_scale     (in_left_v_scale[j]),

                        // Output to Bottom
                        .out_bottom_element (hori_transfer_elem[i+1][j]),
                        .out_bottom_scale   (hori_transfer_scale[i+1][j]),

                        // Output to Right
                        .out_right_element  (vert_transfer_elem[i][j+1]),
                        .out_right_scale    (vert_transfer_scale[i][j+1]),

                        // Output Result
                        .out_fp             (m_out_fp[i][j]),
                        .out_result_ready   (result_ready[i][j])
                    );
                end else begin
                    mxfp_mini_systolic_array #(
                        .MXFP_T_EXP_WIDTH   (MXFP_T_EXP_WIDTH),
                        .MXFP_T_MANT_WIDTH  (MXFP_T_MANT_WIDTH),
                        .MXFP_L_EXP_WIDTH   (MXFP_L_EXP_WIDTH),
                        .MXFP_L_MANT_WIDTH  (MXFP_L_MANT_WIDTH),
                        .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH),
                        .BLOCK_DIM          (BLOCK_DIM),
                        .ACC_FP_EXP_WIDTH   (ACC_FP_EXP_WIDTH),
                        .ACC_FP_MANT_WIDTH  (ACC_FP_MANT_WIDTH)
                    ) default_pe_init (
                        .clk(clk),
                        .rst(rst),

                        // Input from Top Array
                        .in_top_element (hori_transfer_elem[i][j]),
                        .in_top_scale   (hori_transfer_scale[i][j]),
                        .in_top_valid   (columnwise_data_transfer_valid[i][j]),
                        .in_top_ready   (columnwise_data_transfer_ready[i][j]),

                        // Input from Left Array
                        .in_left_element(vert_transfer_elem[i][j]),
                        .in_left_scale  (vert_transfer_scale[i][j]),
                        .in_left_valid  (rowwise_data_transfer_valid[i][j]),
                        .in_left_ready  (rowwise_data_transfer_ready[i][j]),

                        // Output to Bottom
                        .out_bottom_element (hori_transfer_elem[i + 1][j]),
                        .out_bottom_scale   (hori_transfer_scale[i + 1][j]),
                        .out_bottom_valid   (columnwise_data_transfer_valid[i + 1][j]),
                        .out_bottom_ready   (columnwise_data_transfer_ready[i + 1][j]),

                        // Output to Right
                        .out_right_element  (vert_transfer_elem[i][j + 1]),
                        .out_right_scale    (vert_transfer_scale[i][j + 1]),
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