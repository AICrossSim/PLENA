`timescale 1ns / 1ps

/*
Module      : Systolic Array Data Streamer
Timing      : Sequential
Description : It is used to prepare the data input to the systolic array compute unit.
            : It assume the loaded data is in little endian format.
Status      : Under Development
*/

module systolic_data_streamer #(
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

    input   logic [COMPUTE_DIM - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] data_elem_in,
    input   logic [BLOCK_NUM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0] data_scale_in,
    input   logic data_in_valid,
    output  logic data_in_ready,

    input   logic load_en,
    output  logic [COMPUTE_DIM - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] data_elem_out,
    output  logic [BLOCK_NUM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0] data_scale_out,
    output  logic data_out_valid,
    input   logic data_out_ready
);
    localparam COUNTER_BIT_WIDTH = $clog2(COMPUTE_DIM);
    logic [COUNTER_BIT_WIDTH - 1 : 0] store_counter;

    logic [COMPUTE_DIM - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]   data_elem_array_queue [COMPUTE_DIM - 1 : 0];
    logic [BLOCK_NUM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0]                 data_scale_array_queue [COMPUTE_DIM - 1 : 0];
    logic [COMPUTE_DIM - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]   stream_elem_out;
    logic [BLOCK_NUM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0]                 stream_scale_out;
    logic stream_elem_in_ready,     stream_elem_in_valid;
    logic stream_scale_in_ready,    stream_scale_in_valid;


    always_ff @(posedge clk) begin
        if (rst) begin
            for (int i = 0; i < COMPUTE_DIM; i++) begin
                data_elem_array_queue[i] <= '0;
            end
        end else begin
            for (int i = 0; i < COMPUTE_DIM; i++) begin
                if ((store_counter == i & data_in_valid)) begin
                    data_elem_array_queue[store_counter]    <= data_elem_in;
                    data_scale_array_queue[store_counter]   <= data_scale_in;
                    store_counter <= store_counter + 1;
                end else begin
                    if (data_out_ready) begin
                        data_elem_array_queue[i] <= (data_elem_array_queue[i] >> (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1));
                        if (i % BLOCK_DIM == 0) begin
                            data_scale_array_queue[i] <= (data_scale_array_queue[i] >> MXFP_SCALE_WIDTH);
                        end
                    end
                end
                stream_elem_in_valid <= data_in_valid;
                stream_scale_in_valid <= data_in_valid;
            end
        end
    end

    always_comb begin
        if (stream_scale_in_ready & stream_elem_in_ready) begin
            for (int i = 0; i < COMPUTE_DIM; i++) begin
                stream_elem_out[i] = data_elem_array_queue[i][0];
                stream_scale_out[i] = data_scale_array_queue[i][0];
            end
        end
    end

    assign data_in_ready = stream_elem_in_ready & stream_scale_in_ready;

    skid_buffer #(
        .DATA_WIDTH(COMPUTE_DIM * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1))
    ) skid_buffer_elem (
        .clk(clk),
        .rst(rst),
        .data_in            (stream_elem_out),
        .data_in_valid      (load_en),
        .data_in_ready      (stream_elem_in_ready),
        .data_out           (data_elem_out),
        .data_out_valid     (data_out_valid),
        .data_out_ready     (data_out_ready)
    );

    skid_buffer #(
        .DATA_WIDTH(BLOCK_NUM * MXFP_SCALE_WIDTH)
    ) skid_buffer_scale (
        .clk(clk),
        .rst(rst),
        .data_in            (stream_scale_out),
        .data_in_valid      (load_en),
        .data_in_ready      (stream_scale_in_ready),
        .data_out           (data_scale_out),
        .data_out_valid     (data_out_valid),
        .data_out_ready     (data_out_ready)
    );


endmodule