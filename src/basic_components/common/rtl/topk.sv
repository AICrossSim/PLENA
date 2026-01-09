`timescale 1ns / 1ps

/*
Module      : topk
Description : Maintains the top K largest values and their indices from a stream of NUM_DATA elements.
              This module outputs a running top-K. It uses a register_slice to store the 
              current top-K state and handle handshake signals.
*/

module topk #(
    parameter int EXP_WIDTH  = 5,
    parameter int MANT_WIDTH = 10,
    parameter int NUM_DATA   = 16,
    parameter int K          = 4,
    
    localparam int DATA_WIDTH  = EXP_WIDTH + MANT_WIDTH + 1,
    localparam int INDEX_WIDTH = (NUM_DATA > 1) ? $clog2(NUM_DATA) : 1
)(
    input  logic                 clk,
    input  logic                 rst,
    
    // Input interface (ready-valid)
    input  logic                 data_in_valid,
    output logic                 data_in_ready,
    input  logic [DATA_WIDTH-1:0] in_data,
    
    // Output interface (ready-valid)
    output logic [K-1:0][DATA_WIDTH-1:0]  topk_val,
    output logic [K-1:0][INDEX_WIDTH-1:0] topk_idx,
    output logic                 data_out_valid,
    input  logic                 data_out_ready
);

    // --- Internal Signals ---
    logic [INDEX_WIDTH-1:0] count;
    
    // State storage from register slice (packed arrays for concatenation)
    logic [K-1:0][DATA_WIDTH-1:0]  current_topk_val;
    logic [K-1:0][INDEX_WIDTH-1:0] current_topk_idx;
    
    // Combinatorial next state (packed arrays for concatenation)
    logic [K-1:0][DATA_WIDTH-1:0]  next_topk_val;
    logic [K-1:0][INDEX_WIDTH-1:0] next_topk_idx;
    
    logic slice_in_ready, slice_in_valid;
    assign slice_in_valid = (count == NUM_DATA - 1) && data_in_valid && data_in_ready;
    assign data_in_ready = slice_in_ready;

    // --- Counter Logic ---
    always_ff @(posedge clk) begin
        if (rst) begin
            count <= '0;
        end else if (data_in_valid && data_in_ready) begin
            if (count == NUM_DATA - 1)
                count <= '0;
            else
                count <= count + 1'b1;
        end
    end

    // --- Floating Point Comparison Instances ---
    logic [K-1:0] in_gt_current;
    
    for (genvar j = 0; j < K; j++) begin : comp_gen
        fp_compare #(
            .EXP_WIDTH(EXP_WIDTH),
            .MANT_WIDTH(MANT_WIDTH)
        ) comp_inst (
            .data_a(in_data),
            .data_b((count == '0) ? '0 : current_topk_val[j]), // Treat current state as 0 at start of batch
            .a_gt_b(in_gt_current[j]),
            .a_lt_b(),
            .a_eq_b()
        );
    end

    // --- Insertion & Shifting Logic ---
    int insert_idx;
    
    always_comb begin
        // Find the first slot where in_data is larger
        insert_idx = K; // Default: no insertion
        for (int i = 0; i < K; i++) begin
            if (in_gt_current[i]) begin
                insert_idx = i;
                break;
            end
        end

        // Calculate next state
        for (int i = 0; i < K; i++) begin
            if (i < insert_idx) begin
                // Above insertion point: stay same (or zero if new batch)
                next_topk_val[i]     = (count == '0) ? '0 : current_topk_val[i];
                next_topk_idx[i] = (count == '0) ? '0 : current_topk_idx[i];
            end 
            else if (i == insert_idx) begin
                // At insertion point: take in_data
                next_topk_val[i]     = in_data;
                next_topk_idx[i] = count;
            end 
            else begin
                // Below insertion point: shift from previous slot
                next_topk_val[i]     = (count == '0) ? '0 : current_topk_val[i-1];
                next_topk_idx[i] = (count == '0) ? '0 : current_topk_idx[i-1];
            end
        end
    end

    // --- State Storage & Handshaking ---
    // Pack the state into a single flat vector for the register slice
    logic [(K * (DATA_WIDTH + INDEX_WIDTH))-1:0] flat_next_state;
    logic [(K * (DATA_WIDTH + INDEX_WIDTH))-1:0] flat_current_state;

    assign flat_next_state = {next_topk_val, next_topk_idx};

    register_slice #(
        .DATA_WIDTH(K * (DATA_WIDTH + INDEX_WIDTH))
    ) topk_state_reg (
        .clk(clk),
        .rst(rst),
        .data_in(flat_next_state),
        .data_in_valid(data_in_valid),
        .data_in_ready(slice_in_ready),
        .data_out(flat_current_state),
        .data_out_valid(data_out_valid),
        .data_out_ready(data_out_ready)
    );

    // Unpack the state from the flat vector
    assign {current_topk_val, current_topk_idx} = flat_current_state;

    // Assign internal state to output ports
    assign topk_val = current_topk_val;
    assign topk_idx = current_topk_idx;

endmodule
