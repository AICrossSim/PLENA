`timescale 1ns / 1ps

/*
Module      : Floating Point Cumulative Summation (Prefix Scan)
Timing      : Sequential Logic
Description : x1, x1+x2, x1+x2+x3, ..., x1+x2+...+xN
*/

module fp_prefix_scan_syn#(
    parameter int VLEN          = 8,
    parameter int EXP_WIDTH     = 8,
    parameter int MANT_WIDTH    = 23,
    parameter LATENCY_OPT       = 0 // 0 for VLEN to complete the computation, where every element depends on the previously computed results.
)(
    input  logic clk,
    input  logic rst,
    input  logic  [VLEN-1:0][EXP_WIDTH + MANT_WIDTH : 0] vin,
    output logic  [VLEN-1:0][EXP_WIDTH + MANT_WIDTH : 0] vout,
    input  logic in_valid,
    output logic out_valid
);

    localparam LOGN = $clog2(VLEN);
    logic [LOGN:0][VLEN-1:0][EXP_WIDTH + MANT_WIDTH:0] pipe_vect;
    logic [LOGN:0] valid_pipe;

    // Input stage - register the inputs
    always_ff @(posedge clk) begin
        if (rst) begin
            valid_pipe <= 'b0;
            pipe_vect  <= 'b0;
        end else begin
            valid_pipe[0]       <= in_valid;
            if (in_valid) begin
                pipe_vect[0]    <= vin;
            end
            for (int i = 0; i < LOGN; i++) begin
                valid_pipe[i+1] <= valid_pipe[i];
            end
        end
    end

    // Generate adders and pipeline registers for each stage
    genvar i, s;
    generate
        for (s = 0; s < LOGN; s++) begin : stage_gen
            logic [VLEN-1:0][EXP_WIDTH + MANT_WIDTH:0] temp_vect;
            for (i = 0; i < VLEN; i++) begin : adder_gen
                if (i >= (1 << s)) begin: addition_node
                    DW_fp_add_inst #(
                        .EXP_WIDTH(EXP_WIDTH),
                        .MANT_WIDTH(MANT_WIDTH),
                        .IEEE_COMPLIANCE(0)
                    ) fp_add_inst (
                        .clk(clk),
                        .rst(rst),
                        .data_a(pipe_vect[s][i]),
                        .data_b(pipe_vect[s][i-(1<<s)]),
                        .data_in_valid(valid_pipe[s]),
                        .data_in_ready(), // can be left unconnected if not used
                        .data_out(temp_vect[i]),
                        .data_out_valid(), // can be left unconnected if not used
                        .data_out_ready(1'b1) // always ready
                    );
                end else begin: direct_through
                    assign temp_vect[i] = pipe_vect[s][i];
                end
            end
            
            // Logic for stage valid check (combinational)
         always_ff @(posedge clk) begin
                if (rst) begin
                    for (int j = 0; j < VLEN; j++) begin
                        pipe_vect[s+1][j] <= '0;
                    end
                end else begin
                    if (valid_pipe[s]) begin
                       for (int j = 0; j < VLEN; j++) begin
                           pipe_vect[s+1][j] <= temp_vect[j];
                       end
                   end
                end
            end
        end
    endgenerate

    assign vout = pipe_vect[LOGN];
    assign out_valid = valid_pipe[LOGN];
    
endmodule