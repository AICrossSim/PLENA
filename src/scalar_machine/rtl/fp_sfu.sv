`timescale 1ns / 1ps

`include "configuration.svh"
`include "operation.svh"

/*
Module      : Scalar FP Special Function Unit
Timing      : Combinatorial Logic
Description : This module is used for all the FP operations
            : 1. FP Reciprocal 2. FP Sqrt 6. FP Exp
Note        : In this version of the FP_SFU, since we assume that if there are continous FP related 
              Instructions, they are very likely to be data dependent. Therefore, only when the single operation
              is completed, the next operation will be started. Does not support pipelining (Can be optimized in the future)
Status      : Under Development
*/


module fp_sfu #(
    parameter   EXP_WIDTH = 5,
    parameter   MANT_WIDTH = 10,
    parameter   FP_OPERAND_WIDTH = 3
)(
    input   logic clk,
    input   logic rst,
    input   logic [EXP_WIDTH + MANT_WIDTH : 0]  data_in,     
    input   logic [FP_OPERAND_WIDTH - 1 : 0]    reg_waddr, 
    input   S_FP_OP                             operation,         
    output  logic [EXP_WIDTH + MANT_WIDTH : 0]  data_out,
    output  logic [FP_OPERAND_WIDTH - 1 : 0]    stored_reg_waddr, 
    output  logic                               data_out_valid
);


// Status Tracking
S_FP_OP recorded_operation;
logic data_in_valid;
logic data_in_ready;
logic sfu_in_use;
logic data_out_ready;  

always_ff @(posedge clk) begin
    if (rst) begin
        recorded_operation <= STALL_S_FP;
        data_in_valid <= 1'b0;
        stored_reg_waddr <= 'b0;
        data_out_ready <= 1'b0;
    end else begin
        data_out_ready <= 1'b1;
        if (!sfu_in_use & operation != STALL_S_FP) begin
            recorded_operation <= operation;
            stored_reg_waddr <= reg_waddr;
            data_in_valid <= 1'b1;
            sfu_in_use <= 1'b1;
        end else if (data_out_valid & data_out_ready & sfu_in_use) begin
            // At the end of the operation, reset the SFU
            recorded_operation <= STALL_S_FP; 
            data_in_valid <= 1'b0;
        end else if (sfu_in_use) begin
            recorded_operation <= recorded_operation;
            data_in_valid <= 1'b0;
        end else begin
            recorded_operation <= STALL_S_FP;
            data_in_valid <= 1'b0;
        end
    end
end

logic [EXP_WIDTH + MANT_WIDTH : 0] fp_reciprocal_out, fp_exp_out;
logic [EXP_WIDTH + MANT_WIDTH : 0] result_data;
logic result_valid, result_ready;
logic reciprocal_in_valid, exp_in_valid;
logic reciprocal_in_ready, exp_in_ready;
logic reciprocal_out_valid, exp_out_valid;
logic reciprocal_out_ready, exp_out_ready;


always_comb begin
    case (recorded_operation)
        RECI_FP: begin
            result_data             = fp_reciprocal_out;
            reciprocal_in_valid     = data_in_valid;
            data_in_ready           = reciprocal_in_ready;
            result_valid            = reciprocal_out_valid;
            reciprocal_out_ready    = result_ready;
        end

        EXP_FP: begin
            result_data             = fp_exp_out;
            exp_in_valid            = data_in_valid;
            data_in_ready           = exp_in_ready;
            result_valid            = exp_out_valid;
            exp_out_ready           = result_ready;
        end

        default: begin
            result_data             = {(EXP_WIDTH + MANT_WIDTH){1'b0}}; // Default case to avoid latches
            result_valid            = 1'b0;
        end
    endcase
end

    fp_cp_reciprocal #(
        .IN_EXP_WIDTH(EXP_WIDTH),
        .IN_MANT_WIDTH(MANT_WIDTH),
        .OUT_EXP_WIDTH(EXP_WIDTH),
        .OUT_MANT_WIDTH(MANT_WIDTH)
    ) scalar_fp_reciprocal_init (
        .clk(clk),
        .rst(rst),
        .data_in_valid  (reciprocal_in_valid),
        .data_in_ready  (reciprocal_in_ready),
        .data_in        (data_in),
        .data_out_valid (reciprocal_out_valid),
        .data_out_ready (reciprocal_out_ready),
        .data_out       (fp_reciprocal_out)
    );

    fp_cp_exp #(
        .IN_EXP_WIDTH(EXP_WIDTH),
        .IN_MANT_WIDTH(MANT_WIDTH),
        .OUT_EXP_WIDTH(EXP_WIDTH),
        .OUT_MANT_WIDTH(MANT_WIDTH)
    ) scalar_fp_exp_init (
        .clk(clk),
        .rst(rst),
        .data_in_valid  (exp_in_valid),
        .data_in_ready  (exp_in_ready),
        .data_in        (data_in),
        .data_out_valid (exp_out_valid),
        .data_out_ready (exp_out_ready),
        .data_out       (fp_exp_out)
    );

    skid_buffer #(
        .DATA_WIDTH(EXP_WIDTH + MANT_WIDTH + 1)
    ) register_slice (
        .clk           (clk),
        .rst           (rst),                        
        .data_in       (result_data),                      // flattened LEVEL_OUT_DIM * LEVEL_OUT_WIDTH
        .data_in_valid (result_valid),
        .data_in_ready (result_ready),
        .data_out      (data_out),
        .data_out_valid(data_out_valid),
        .data_out_ready(data_out_ready)
    );

endmodule