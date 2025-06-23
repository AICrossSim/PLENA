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
    logic [COUNTER_BIT_WIDTH : 0] store_counter;
    logic [COUNTER_BIT_WIDTH : 0] clear_counter;

    logic [COMPUTE_DIM - 1 : 0][FP_EXP_WIDTH + FP_MANT_WIDTH : 0]       data_array_queue [COMPUTE_DIM - 1 : 0];
    logic [COMPUTE_DIM - 1 : 0][FP_EXP_WIDTH + FP_MANT_WIDTH : 0]       stream_data_out;
    logic stream_in_ready,     stream_in_valid;
    logic stream_in_valid_hold;
    logic stream_data_out_valid;
    logic p1_stream_in_ready;

    typedef enum logic [1:0] { 
        IDLE = 2'b00,
        FILLING = 2'b01,
        CLEARING = 2'b10
    } stream_state_t;

    stream_state_t state, next_state;

    always_ff @(posedge clk) begin
        if (rst) begin
            for (int i = 0; i < COMPUTE_DIM; i++) begin
                data_array_queue[i] <= '0;
            end
            store_counter   <= '0;
            clear_counter   <= '0;
            stream_in_valid <= 1'b1;
            state           <= IDLE;
            p1_stream_in_ready <= 1'b0;
            stream_in_valid_hold <= 1'b0;
        end else begin
            state <= next_state;
            p1_stream_in_ready <= stream_in_ready;
            case (state)
                IDLE: begin
                    stream_in_valid <= 1'b1;
                    if (data_in_valid & stream_in_ready) begin
                        for (int i = 0; i < COMPUTE_DIM; i++) begin
                            if ((store_counter == i)) begin
                                data_array_queue[store_counter]     <= data_in;
                                store_counter                       <= store_counter + 'b1;
                            end else begin
                                data_array_queue[i] <= (data_array_queue[i] >> (FP_EXP_WIDTH + FP_MANT_WIDTH + 1));
                            end
                        end
                    end
                end
                FILLING: begin
                    if (store_counter == COMPUTE_DIM) begin
                        store_counter <= '0;
                    end else begin
                        if (data_in_valid & stream_in_ready) begin
                            for (int i = 0; i < COMPUTE_DIM; i++) begin
                                if ((store_counter == i)) begin
                                    data_array_queue[store_counter]     <= data_in;
                                    store_counter                       <= store_counter + 'b1;
                                end else begin
                                    data_array_queue[i] <= (data_array_queue[i] >> (FP_EXP_WIDTH + FP_MANT_WIDTH + 1));
                                end
                            end
                            stream_in_valid <= 1'b1;
                            if (stream_in_valid_hold) begin
                                stream_in_valid_hold <= 1'b0;
                            end
                        end else begin
                            if (stream_in_valid & !stream_in_ready) begin
                                stream_in_valid_hold <= 1'b1;
                            end else if (stream_in_valid_hold & stream_in_ready) begin
                                stream_in_valid_hold <= 1'b0;
                            end else begin
                                stream_in_valid <= 1'b0;
                            end
                        end
                    end
                end
                CLEARING: begin
                    if (stream_in_ready) begin
                        for (int i = 0; i < COMPUTE_DIM; i++) begin
                            data_array_queue[i] <= (data_array_queue[i] >> (FP_EXP_WIDTH + FP_MANT_WIDTH + 1));
                        end
                        clear_counter <= clear_counter + 'b1;   
                        stream_in_valid <= 1'b1;  
                        if (stream_in_valid_hold) begin
                            stream_in_valid_hold <= 1'b0;
                        end
                        if (clear_counter == COMPUTE_DIM) begin
                            clear_counter <= '0;
                        end
                    end else begin
                        if (stream_in_valid) begin
                            stream_in_valid_hold <= 1'b1;
                        end
                        stream_in_valid <= 1'b0;
                    end
                    
                end
            endcase
        end
    end

    always_comb begin
        for (int i = 0; i < COMPUTE_DIM; i++) begin
            stream_data_out[i] = data_array_queue[i][0];
        end
        case (state)
            IDLE: begin
                if (data_in_valid & stream_in_ready) begin
                    next_state = FILLING;
                end else begin
                    next_state = IDLE;
                end
            end
            FILLING: begin
                if (store_counter == COMPUTE_DIM) begin 
                    if (data_in_valid & stream_in_ready) begin
                        next_state = FILLING;
                    end else begin
                        next_state = CLEARING;
                    end
                end else begin
                    next_state = FILLING;
                end
            end
            CLEARING: begin
                if (data_in_valid & stream_in_ready) begin
                    next_state = FILLING;
                end else if (clear_counter == COMPUTE_DIM) begin
                    next_state = IDLE;
                end else begin
                    next_state = CLEARING;
                end
            end
            default: begin
                next_state = IDLE;
            end
        endcase

        if (stream_in_valid_hold) begin
            stream_data_out_valid = (stream_in_ready) ? 1'b1 : 1'b0;
        end else begin
            stream_data_out_valid = stream_in_valid;
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
        .data_in_valid      (stream_data_out_valid),
        .data_in_ready      (stream_in_ready),
        .data_out           (data_out),
        .data_out_valid     (data_out_valid),
        .data_out_ready     (data_out_ready)
    );

endmodule