`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Matrix Machine Module
Timing      : Sequential, Takes x cycles to compute the dot product
Description : This module conducts the operation m(MLEN, MLEN) @ v(MLEN, 1) + o (MLEN, 1)
Status      : Under Testing
*/


module matrix_machine #(
    // MX-FP Data Format
    parameter   MXFP_MANT_WIDTH   = 8,
    parameter   MXFP_EXP_WIDTH    = 4,
    parameter   MXFP_SCALE_WIDTH = 8,

    // Dimensions
    parameter   MLEN              = 8,
    parameter   BLOCK_DIM         = 4,
    localparam  BLOCK_NUM         = MLEN / BLOCK_DIM,

    // Precision Control
    parameter   PRODUCT_EXT_EXP_WIDTH   = 1,
    parameter   PRODUCT_EXT_MANT_WIDTH  = 0,
    parameter   BLOCK_ADD_EXT_EXP_WIDTH       = 1,  // Note: this param control precision for both blockwise addition within adder tree and the blockwise adder
    parameter   BLOCK_ADD_EXT_MANT_WIDTH      = 0,
    parameter   FP_ADD_EXT_EXP_WIDTH       = 1,
    parameter   FP_ADD_EXT_MANT_WIDTH      = 0,

    // Intermediate FP Control
    parameter   ROUND_FP_EN            = 0,
    parameter   ROUND_FP_EXP_WIDTH     = 4,
    parameter   ROUND_FP_MANT_WIDTH    = 3, 

    // Memory Dimensions
    parameter   Matrix_Parallel_Rd_Dim = 2,

    // Offset Management
    parameter   ADDR_WIDTH = 32,

    // Pipeline Stages
    localparam  PIPELINE_STAGES = 5,
    localparam  CYC_TO_COMPLETE_LOADING = 2
) (
    input   logic   clk,
    input   logic   rst,

    // Execution Control
    input   M_OP    matrix_opcode,
    output  logic   ready_for_next_op,

    // Offset Addressing
    input  logic                              set_offset_addr,
    input  logic [ADDR_WIDTH-1:0]             offset_addr,
    output logic [ADDR_WIDTH-1:0]             offset_addr_out,

    // Matix - row-major order
    input  logic [MLEN*Matrix_Parallel_Rd_Dim-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      m_element,
    input  logic [BLOCK_NUM*Matrix_Parallel_Rd_Dim-1:0]          [MXFP_SCALE_WIDTH-1:0]         m_scale,
    input  logic                   m_valid,
    output logic                   m_ready,

    // Vector - row-major order
    input  logic [MLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      v_element,
    input  logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                      v_scale,
    input  logic                   v_valid,
    output logic                   v_ready,

    // Offset - row-major order
    input  logic [MLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      o_element,
    input  logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                      o_scale,
    input  logic                    o_valid,
    output logic                    o_ready,

    // Output
    input  logic [ADDR_WIDTH-1:0]             result_waddr,
    input  logic result_waddr_update,
    
    output logic [MLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      out_element,
    output logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                     out_scale,
    output logic                            out_valid,
    input  logic                            out_ready,
    output logic [ADDR_WIDTH-1:0]             m_waddr,
    output logic                              m_wreq
    
);

initial begin

end

// Fetch Control
logic clear_m;
logic buffer_ready_m, buffer_ready_v, buffer_ready_o;
assign m_ready  = (matrix_opcode != STALL_M) ? buffer_ready_m : 1'b0;
assign v_ready  = (matrix_opcode != STALL_M) ? buffer_ready_v : 1'b0;
assign o_ready  = (matrix_opcode == MV_O)    ? buffer_ready_o : 1'b0;

M_OP pipeline_track [PIPELINE_STAGES-1:0];
logic [ADDR_WIDTH-1:0] pipeline_result_addr [PIPELINE_STAGES-1:0];


always_ff @(posedge clk or negedge rst) begin
    if (!rst) begin
        for (int i = 0; i < PIPELINE_STAGES; i++) begin
            pipeline_track[i] <= STALL_M;
            pipeline_result_addr[i] <= 'b0;
        end
        offset_addr_out <= 'b0;
    end else begin
        
        pipeline_track[0] <= matrix_opcode;
        pipeline_result_addr[0] <= (result_waddr_update == 1'b1) ? result_waddr : 'b0;
        
        for (int i = 1; i < PIPELINE_STAGES; i++) begin
            pipeline_track[i] <= pipeline_track[i-1];
            pipeline_result_addr[i] <= pipeline_result_addr[i-1];
        end

        // Set offset address
        if (set_offset_addr) begin
            offset_addr_out <= offset_addr;
        end
    end
end

always_comb begin
    if (pipeline_track[CYC_TO_COMPLETE_LOADING] == MV) begin
        if (collect_m_valid && stored_v_valid) begin
            ready_for_next_op = 1'b1;
        end else begin
            ready_for_next_op = 1'b0;
        end
    end else if (pipeline_track[CYC_TO_COMPLETE_LOADING] == MV_O) begin
        if (collect_m_valid && stored_v_valid && stored_o_valid) begin
            ready_for_next_op = 1'b1;
        end else begin
            ready_for_next_op = 1'b0;
        end
    end
end


// Matrix Buffering
// Element Collector
logic [MLEN*MLEN-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      collect_m_element;
logic [MLEN*BLOCK_NUM-1:0]          [MXFP_SCALE_WIDTH-1:0]       collect_m_scale;

logic collect_in_m_ele_ready,   collect_in_m_scale_ready;
logic collect_in_m_ele_valid,   collect_in_m_scale_valid;
logic collect_m_ele_ready,      collect_m_scale_ready;
logic collect_m_ele_valid,      collect_m_scale_valid;
logic collect_m_valid,          collect_m_ready;

split_n #(
    .N(2)
) eb_split_i (
    .data_in_valid (m_valid),
    .data_in_ready (buffer_ready_m),
    .data_out_valid({collect_in_m_ele_valid, collect_in_m_scale_valid}),
    .data_out_ready({collect_in_m_ele_ready, collect_in_m_scale_ready})
);

matrix_collector #(
    .DATA_WIDTH((MXFP_MANT_WIDTH + MXFP_EXP_WIDTH + 1) * MLEN),
    .MLEN(MLEN),
    .Collect_Dim(Matrix_Parallel_Rd_Dim)
) element_collect (
    .clk(clk),
    .rst_n(rst),
    .clear(clear_m),

    // Input
    .in_data(m_element),
    .in_valid(collect_in_m_ele_valid),
    .in_ready(collect_in_m_ele_ready),

    // Output
    .out_matrix(collect_m_element),
    .out_valid(collect_m_ele_valid),
    .out_ready(collect_m_ele_ready)
);

// Scale Collector
matrix_collector #(
    .DATA_WIDTH(MXFP_SCALE_WIDTH * BLOCK_NUM),
    .MLEN(MLEN),
    .Collect_Dim(Matrix_Parallel_Rd_Dim)
) scale_collect (
    .clk(clk),
    .rst_n(rst),

    // Input
    .in_data(m_scale),
    .in_valid(collect_in_m_scale_valid),
    .in_ready(collect_in_m_scale_ready),

    // Output
    .out_matrix(collect_m_scale),
    .out_valid(collect_m_scale_valid),
    .out_ready(collect_m_scale_ready)
);

join_n #(
    .NUM_HANDSHAKES (2)
) join_m_element (
    .data_in_valid({collect_m_ele_valid, collect_m_scale_valid}),
    .data_in_ready({collect_m_ele_ready, collect_m_scale_ready}),
    .data_out_valid(collect_m_valid),
    .data_out_ready(collect_m_ready)
);


// Multiplicand Vector Buffering
logic [MLEN-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      stored_v_element;
logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]       stored_v_scale;
logic stored_v_in_ele_ready, stored_v_in_scale_ready;
logic stored_v_in_ele_valid, stored_v_in_scale_valid;
logic stored_v_ele_ready, stored_v_scale_ready;
logic stored_v_ele_valid, stored_v_scale_valid;
logic stored_v_valid, stored_v_ready;

split_n #(
    .N(2)
) v_split_i (
    .data_in_valid (v_valid),
    .data_in_ready (buffer_ready_v),
    .data_out_valid({stored_v_in_ele_valid, stored_v_in_scale_valid}),
    .data_out_ready({stored_v_in_ele_ready, stored_v_in_scale_ready})
);

skid_buffer #(
    .DATA_WIDTH(MLEN * (MXFP_MANT_WIDTH + MXFP_EXP_WIDTH+1))
) multiplicand_vec_element_buffer (
    .clk(clk),
    .rst(!rst),

    // Input
    .data_in(v_element),
    .data_in_valid(stored_v_in_ele_valid),
    .data_in_ready(stored_v_in_ele_ready),

    // Output
    .data_out(stored_v_element),
    .data_out_valid(stored_v_ele_valid),
    .data_out_ready(stored_v_ele_ready)
);

skid_buffer #(
    .DATA_WIDTH(BLOCK_NUM * MXFP_SCALE_WIDTH)
) multiplicand_vec_scale_buffer (
    .clk(clk),
    .rst(!rst),

    // Input
    .data_in(v_scale),
    .data_in_valid(stored_v_in_scale_valid),
    .data_in_ready(stored_v_in_scale_ready),

    // Output
    .data_out(stored_v_scale),
    .data_out_valid(stored_v_scale_valid),
    .data_out_ready(stored_v_scale_ready)
);

join_n #(
    .NUM_HANDSHAKES (2)
) join_v_element (
    .data_in_valid({stored_v_ele_valid, stored_v_scale_valid}),
    .data_in_ready({stored_v_ele_ready, stored_v_scale_ready}),
    .data_out_valid(stored_v_valid),
    .data_out_ready(stored_v_ready)
);


// Offset Vector Buffering
logic [MLEN-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      stored_o_element;
logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]       stored_o_scale;
logic stored_o_in_ele_ready, stored_o_in_scale_ready;
logic stored_o_in_ele_valid, stored_o_in_scale_valid;
logic stored_o_ele_ready, stored_o_scale_ready;
logic stored_o_ele_valid, stored_o_scale_valid;
logic stored_o_valid, stored_o_ready;

split_n #(
    .N(2)
) o_split_i (
    .data_in_valid (o_valid),
    .data_in_ready (buffer_ready_o),
    .data_out_valid({stored_o_in_ele_valid, stored_o_in_scale_valid}),
    .data_out_ready({stored_o_in_ele_ready, stored_o_in_scale_ready})
);

skid_buffer #(
    .DATA_WIDTH(MLEN * (MXFP_MANT_WIDTH + MXFP_EXP_WIDTH + 1))
) offset_vec_element_buffer (
    .clk(clk),
    .rst(!rst),

    // Input
    .data_in(o_element),
    .data_in_valid(stored_o_in_ele_valid),
    .data_in_ready(stored_o_in_ele_ready),

    // Output
    .data_out(stored_o_element),
    .data_out_valid(stored_o_ele_valid),
    .data_out_ready(stored_o_ele_ready)
);

skid_buffer #(
    .DATA_WIDTH(BLOCK_NUM * MXFP_SCALE_WIDTH)
) offset_vec_scale_buffer (
    .clk(clk),
    .rst(!rst),

    // Input
    .data_in(o_scale),
    .data_in_valid(stored_o_in_scale_valid),
    .data_in_ready(stored_o_in_scale_ready),

    // Output
    .data_out(stored_o_scale),
    .data_out_valid(stored_o_scale_valid),
    .data_out_ready(stored_o_scale_ready)
);

join_n #(
    .NUM_HANDSHAKES (2)
) join_o_element (
    .data_in_valid({stored_o_ele_valid, stored_o_scale_valid}),
    .data_in_ready({stored_o_ele_ready, stored_o_scale_ready}),
    .data_out_valid(stored_o_valid),
    .data_out_ready(stored_o_ready)
);

// Control Logic
logic   prod_valid, prod_ready;
logic [MLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      prod_element;
logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                     prod_scale;

// Matrix - Vector multiplication Unit
mx_fp_mv #(
    .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
    .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
    .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),

    .COMPUTE_DIM(MLEN),
    .BLOCK_DIM(BLOCK_DIM),

    .PRODUCT_EXT_EXP_WIDTH(PRODUCT_EXT_EXP_WIDTH),
    .PRODUCT_EXT_MANT_WIDTH(PRODUCT_EXT_MANT_WIDTH),
    .BLOCK_ADD_EXT_EXP_WIDTH(BLOCK_ADD_EXT_EXP_WIDTH),
    .BLOCK_ADD_EXT_MANT_WIDTH(BLOCK_ADD_EXT_MANT_WIDTH),
    .FP_ADD_EXT_EXP_WIDTH(FP_ADD_EXT_EXP_WIDTH),
    .FP_ADD_EXT_MANT_WIDTH(FP_ADD_EXT_MANT_WIDTH),

    .OUTPUT_FP_ROUND_EN(ROUND_FP_EN),
    .ROUND_FP_EXP_WIDTH(ROUND_FP_EXP_WIDTH),
    .ROUND_FP_MANT_WIDTH(ROUND_FP_MANT_WIDTH)
) mx_fp_mv (
    .clk(clk),
    .rst(rst),

    // input port A
    .m_element(collect_m_element),
    .m_scale(collect_m_scale),
    .m_valid(collect_m_valid),
    .m_ready(collect_m_ready),

    // input port B
    .v_element(stored_v_element),
    .v_scale(stored_v_scale),
    .v_valid(stored_v_valid),
    .v_ready(stored_v_ready),

    // output port
    .out_element(prod_element),
    .out_scale(prod_scale),
    .out_valid(prod_valid),
    .out_ready(prod_ready)
);

// offset addition
logic [MLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      acc_element;
logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                     acc_scale;
logic acc_in_valid, acc_in_ready;
logic acc_out_valid, acc_out_ready;


always_comb begin
    if (pipeline_track[PIPELINE_STAGES] == MV_O) begin
        out_element = acc_element;
        out_scale   = acc_scale;
        out_valid   = acc_out_valid;
        acc_in_valid    = prod_valid;
        acc_out_ready   = out_ready;
        prod_ready   = acc_in_ready;
    end else if( pipeline_track[PIPELINE_STAGES] == MV) begin
        out_element     = prod_element;
        out_scale       = prod_scale;
        out_valid       = prod_valid;
        acc_in_valid    = 1'b0;
        acc_out_ready   = 1'b0;
        prod_ready   = out_ready;
    end else begin
        out_element = {MLEN{1'b0}};
        out_scale   = {BLOCK_NUM{1'b0}};
        out_valid   = 1'b0;
    end
end

generate;
    for(genvar i=0; i < BLOCK_NUM; i++)begin
        mx_fp_blockwise_adder #(
            .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
            .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
            .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),

            .BLOCK_DIM(BLOCK_DIM),

            .EXT_EXP_WIDTH(BLOCK_ADD_EXT_EXP_WIDTH),
            .EXT_MANT_WIDTH(BLOCK_ADD_EXT_MANT_WIDTH)
        ) mx_fp_blockwise_adder (
            .clk(clk),
            .rst(rst),

            // Port A
            .a_element_data_in(prod_element[i]),
            .a_scale_data_in(prod_scale[i]),
            .a_data_in_valid(acc_in_valid),
            .a_data_in_ready(acc_in_ready),

            // Port B
            .b_element_data_in(stored_o_element[i]),
            .b_scale_data_in(stored_o_scale[i]),
            .b_data_in_valid(stored_o_valid),
            .b_data_in_ready(stored_o_ready),

            // Output
            .element_data_out(acc_element[i]),
            .scale_data_out(acc_scale[i]),
            .data_out_valid(acc_out_valid),
            .data_out_ready(acc_out_ready)
        );
    end
endgenerate



endmodule