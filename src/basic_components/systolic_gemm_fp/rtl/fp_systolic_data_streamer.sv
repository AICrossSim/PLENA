`timescale 1ns / 1ps

/*
Module      : Systolic Array Data Streamer
Timing      : Sequential
Description : It is used to prepare the data input to the systolic array compute unit.
            : It assume the loaded data is in little endian format.
Status      : Under Development
*/

module fp_systolic_data_streamer #(
    // Data Format
    parameter FP_EXP_WIDTH    = 8,
    parameter FP_MANT_WIDTH   = 7,
    // Dimension
    parameter COMPUTE_DIM           = 8
)(
    input   logic clk,
    input   logic rst,
    // Data Input
    input   logic [COMPUTE_DIM - 1 : 0][FP_EXP_WIDTH + FP_MANT_WIDTH : 0] data_in,
    input   logic data_in_valid,
    output  logic data_in_ready,
    // Data Output
    output  logic [COMPUTE_DIM - 1 : 0][FP_EXP_WIDTH + FP_MANT_WIDTH : 0] data_out,
    output  logic data_out_valid,
    input   logic data_out_ready
);
    localparam COUNTER_BIT_WIDTH = $clog2(COMPUTE_DIM);
    logic [COUNTER_BIT_WIDTH - 1 : 0] store_counter;

    logic [COMPUTE_DIM - 1 : 0][FP_EXP_WIDTH + FP_MANT_WIDTH : 0]       data_array_queue [COMPUTE_DIM - 1 : 0];
    logic [COMPUTE_DIM - 1 : 0][FP_EXP_WIDTH + FP_MANT_WIDTH : 0]       stream_data_out;
    logic stream_in_ready,     stream_in_valid;

    always_ff @(posedge clk) begin
        if (rst) begin
            for (int i = 0; i < COMPUTE_DIM; i++) begin
                data_array_queue[i] <= '0;
            end
            store_counter   <= '0;
            stream_in_valid <= '0;
        end else begin
            if (data_in_valid & stream_in_ready) begin
                for (int i = 0; i < COMPUTE_DIM; i++) begin
                    if ((store_counter == i)) begin
                        data_array_queue[store_counter]    <= data_in;
                        store_counter       <= store_counter + 'b1;
                    end else begin
                        data_array_queue[i] <= (data_array_queue[i] >> (FP_EXP_WIDTH + FP_MANT_WIDTH + 1));
                    end
                end
            end
            stream_in_valid <= data_in_valid;
        end
    end

    always_comb begin
        for (int i = 0; i < COMPUTE_DIM; i++) begin
            stream_data_out[i] = data_array_queue[i][0];
        end
    end

    assign data_in_ready = stream_in_ready;
    logic data_element_out_valid, data_scale_out_valid;
    logic data_element_out_ready, data_scale_out_ready;

    skid_buffer #(
        .DATA_WIDTH(COMPUTE_DIM * (FP_EXP_WIDTH + FP_MANT_WIDTH + 1))
    ) skid_buffer_elem (
        .clk(clk),
        .rst(rst),
        .data_in            (stream_data_out),
        .data_in_valid      (stream_in_valid),
        .data_in_ready      (stream_in_ready),
        .data_out           (data_out),
        .data_out_valid     (data_out_valid),
        .data_out_ready     (data_out_ready)
    );

endmodule