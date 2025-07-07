`timescale 1ns / 1ps

/*
Module      : Systolic Array TOP Data Streamer
Timing      : Sequential
Description : It is used to prepare the data input to the systolic array compute unit.
            : It assume the loaded data is in little endian format.
Status      : Under Development
*/

module mxfp_systolic_top_streamer #(
    // MX-FP Data Format
    parameter MXFP_EXP_WIDTH        = 4,
    parameter MXFP_MANT_WIDTH       = 3,
    parameter MXFP_SCALE_WIDTH      = 8,
    parameter BLOCK_DIM             = 4,
    // Accumulator Data Format
    parameter ACC_FP_EXP_WIDTH      = 8,
    parameter ACC_FP_MANT_WIDTH     = 7,
    // Dimension
    parameter   COMPUTE_DIM           = 8,
    localparam  BLOCK_NUM            = COMPUTE_DIM / BLOCK_DIM
)(
    input   logic clk,
    input   logic rst,
    input   logic transposed, // 0 for 
    // Data Input
    input   logic [COMPUTE_DIM - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]   data_elem_in,
    input   logic [COMPUTE_DIM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0]               data_scale_in,
    input   logic data_in_valid,
    output  logic data_in_ready,
    // Data Output
    output  logic [COMPUTE_DIM - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]   data_elem_out,
    output  logic [COMPUTE_DIM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0]               data_scale_out,
    output  logic data_out_valid,
    input   logic data_out_ready
);
    localparam COUNTER_BIT_WIDTH = $clog2(COMPUTE_DIM);
    localparam PER_BLOCK_ELE_WIDTH = BLOCK_DIM * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1);
    localparam BLOCK_BITWIDTH = $clog2(BLOCK_DIM);

    logic [COUNTER_BIT_WIDTH : 0] store_counter;
    logic [COUNTER_BIT_WIDTH : 0] clear_counter;
    logic [COUNTER_BIT_WIDTH : 0] scale_store_counter;

    logic [COMPUTE_DIM - 1 : 0][COMPUTE_DIM - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]   data_elem_array_queue;
    logic [COMPUTE_DIM - 1 : 0][COMPUTE_DIM - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]   next_data_elem_array_queue;
    logic [COMPUTE_DIM - 1 : 0][COMPUTE_DIM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0]               data_scale_array_queue;
    logic [COMPUTE_DIM - 1 : 0][COMPUTE_DIM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0]               next_data_scale_array_queue;
    logic [COMPUTE_DIM - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]                        stream_elem_out;
    logic [COMPUTE_DIM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0]                                    stream_scale_out;
    logic stream_elem_in_ready,     stream_elem_in_valid;
    logic stream_scale_in_ready,    stream_scale_in_valid;
    logic stream_in_ready,          stream_in_valid;
    logic stream_in_valid_hold;
    logic stream_data_out_valid;

    typedef enum logic [1:0] { 
        IDLE = 2'b00,
        FILLING = 2'b01,
        CLEARING = 2'b10
    } stream_state_t;

    stream_state_t p1_state, state, next_state; 

    always_comb begin
        for (int i = 0; i < COMPUTE_DIM; i++) begin
            stream_elem_out[i]  = data_elem_array_queue[i][0];
        end
        for (int j = 0; j < BLOCK_NUM; j++) begin
            stream_scale_out[j] = data_scale_array_queue[j][0];
        end

        case (state)
            IDLE: begin
                if (data_in_valid & stream_in_ready) begin
                    next_state = FILLING;
                    for (int i = 0; i < COMPUTE_DIM; i++) begin
                        next_data_elem_array_queue[i] = (data_elem_array_queue[i] >> (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1));
                        next_data_elem_array_queue[i][i] = data_elem_in[i];
                        next_data_scale_array_queue[i] = (data_scale_array_queue[i] >> MXFP_SCALE_WIDTH);
                        next_data_scale_array_queue[i][i] = data_scale_in[i];
                    end
                end else begin
                    next_state = IDLE;
                end
            end
            FILLING: begin
                if (data_in_valid & stream_in_ready) begin
                    for (int i = 0; i < COMPUTE_DIM; i++) begin
                        next_data_elem_array_queue[i] = (data_elem_array_queue[i] >> (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1));
                        next_data_elem_array_queue[i][i] = data_elem_in[i];
                        next_data_scale_array_queue[i] = (data_scale_array_queue[i] >> MXFP_SCALE_WIDTH);
                        next_data_scale_array_queue[i][i] = data_scale_in[i];
                    end
                end
                if (store_counter == COMPUTE_DIM - 1 & stream_in_ready) begin 
                    next_state = CLEARING;
                end else begin
                    next_state = FILLING;
                end
            end
            CLEARING: begin
                if (stream_in_ready) begin
                    for (int i = 0; i < COMPUTE_DIM; i++) begin
                        next_data_elem_array_queue [i] = (data_elem_array_queue [i] >> (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1));
                        next_data_scale_array_queue[i] = (data_scale_array_queue[i] >> MXFP_SCALE_WIDTH);
                    end
                end
                if (p1_state != FILLING & data_in_valid & stream_in_ready) begin 
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


    always_ff @(posedge clk) begin
        if (rst) begin
            data_elem_array_queue <= '0;
            data_scale_array_queue <= '0;
            store_counter   <= '0;
            clear_counter   <= '0;
            stream_in_valid <= 1'b0;
            state           <= IDLE;
            p1_state        <= IDLE;
            stream_in_valid_hold <= 1'b0;
        end else begin
            state <= next_state;
            p1_state <= state;
            case (state)
                IDLE: begin
                    // First storage.
                    if (data_in_valid & stream_in_ready) begin
                        data_elem_array_queue <= next_data_elem_array_queue;
                        data_scale_array_queue <= next_data_scale_array_queue;
                        stream_in_valid <= 1'b1;
                        store_counter <= 'b1;
                    end else begin
                        stream_in_valid <= 1'b0;
                    end
                end
                FILLING: begin
                    if (data_in_valid & stream_in_ready) begin
                        data_elem_array_queue <= next_data_elem_array_queue;
                        data_scale_array_queue <= next_data_scale_array_queue;
                        stream_in_valid <= 1'b1;
                        if (stream_in_valid_hold) begin
                            stream_in_valid_hold <= 1'b0;
                        end
                        store_counter                       <= store_counter + 'b1;
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
                CLEARING: begin
                    store_counter <= '0;
                    if (stream_in_ready) begin
                        data_elem_array_queue   <= next_data_elem_array_queue;
                        data_scale_array_queue  <= next_data_scale_array_queue;
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


    split_n #(
        .N(2)
    ) split_init (
        .data_in_valid(stream_data_out_valid),
        .data_in_ready(stream_in_ready),
        .data_out_valid({stream_elem_in_valid, stream_scale_in_valid}),
        .data_out_ready({stream_elem_in_ready, stream_scale_in_ready})
    );   
    
    assign data_in_ready = stream_in_ready;
    logic data_element_out_valid, data_scale_out_valid;
    logic data_element_out_ready, data_scale_out_ready;

    skid_buffer #(
        .DATA_WIDTH(COMPUTE_DIM * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1))
    ) skid_buffer_elem (
        .clk(clk),
        .rst(rst),
        .data_in            (stream_elem_out),
        .data_in_valid      (stream_elem_in_valid),
        .data_in_ready      (stream_elem_in_ready),
        .data_out           (data_elem_out),
        .data_out_valid     (data_element_out_valid),
        .data_out_ready     (data_element_out_ready)
    );

    skid_buffer #(
        .DATA_WIDTH(COMPUTE_DIM * MXFP_SCALE_WIDTH)
    ) skid_buffer_scale (
        .clk(clk),
        .rst(rst),
        .data_in            (stream_scale_out),
        .data_in_valid      (stream_scale_in_valid),
        .data_in_ready      (stream_scale_in_ready),
        .data_out           (data_scale_out),
        .data_out_valid     (data_scale_out_valid),
        .data_out_ready     (data_scale_out_ready)
    );

    join2 #(        
    ) join_data_out (
        .data_in_valid({data_element_out_valid, data_scale_out_valid}),
        .data_in_ready({data_element_out_ready, data_scale_out_ready}),
        .data_out_valid(data_out_valid),
        .data_out_ready(data_out_ready)
    );


endmodule