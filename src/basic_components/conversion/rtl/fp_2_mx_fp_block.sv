`timescale 1ns / 1ps

/*
Module      : Convertion Units Floating Point with Configurable Precision to MX-FP
Timing      : Sequential, Takes 2 cycle to compute the dot product
Description : 
                Pipeline Stage 1 : Extracting the maximum exponent from the input data
                Pipeline Stage 2 : Normalizing the input data and converting it to MX-FP format
Status      : Passed Simple Tests
*/


module fp_2_mx_fp_block #(
    parameter BLOCK_DIM = 8, 
    parameter FP_MANT_WIDTH = 3,
    parameter FP_EXP_WIDTH = 4,

    parameter MX_FP_MANT_WIDTH = 3,
    parameter MX_FP_EXP_WIDTH = 4,
    parameter MXFP_SCALE_WIDTH = 8
)(
    input   logic clk,
    input   logic rst,
    input   logic [BLOCK_DIM-1:0][FP_MANT_WIDTH + FP_EXP_WIDTH : 0] data_in,
    input   logic data_in_valid,
    output  logic data_in_ready,

    output  logic [BLOCK_DIM-1:0][MX_FP_MANT_WIDTH + MX_FP_EXP_WIDTH : 0] element_data_out,
    output  logic [MXFP_SCALE_WIDTH-1:0] scale_data_out,
    output  logic mx_fp_data_out_valid,
    input   logic mx_fp_data_out_ready
);

    localparam FP_OFFSET =          (1 << (FP_EXP_WIDTH-1)) - 1;
    localparam MXFP_SCALE_OFFSET =  (1 << (MXFP_SCALE_WIDTH-1)) - 1;


    // Split input into sgn, exp, man fields.
    logic                               fp_sgns [BLOCK_DIM];
    logic unsigned [BLOCK_DIM -1:0][FP_EXP_WIDTH - 1:0] fp_exps;
    logic unsigned [FP_EXP_WIDTH - 1:0] exp_max;
    logic unsigned [BLOCK_DIM -1:0][FP_MANT_WIDTH - 1:0] fp_mans;

    generate;
        for (genvar i =0; i < BLOCK_DIM; i=i+1) begin
            assign fp_sgns[i] = data_in[i][FP_EXP_WIDTH + FP_MANT_WIDTH];
            assign fp_exps[i] = data_in[i][FP_EXP_WIDTH + FP_MANT_WIDTH - 1 : FP_MANT_WIDTH];
            assign fp_mans[i] = data_in[i][FP_MANT_WIDTH-1:0];
        end
    endgenerate

    unsigned_max #(
        .width(FP_EXP_WIDTH),
        .length(BLOCK_DIM),
        .flop_output(0)
    ) u0_exp_max (
        .clk(clk),
        .input_data(fp_exps),
        .max_val(exp_max)
    );
    
    logic unsigned [MXFP_SCALE_WIDTH - 1:0] p1_e_max;
    logic                               p1_fp_sgns [BLOCK_DIM];
    logic unsigned [BLOCK_DIM-1:0][FP_EXP_WIDTH - 1:0]  p1_fp_exps;
    logic unsigned [BLOCK_DIM-1:0][FP_MANT_WIDTH - 1:0] p1_fp_mans;

    // Setting the lower bound
    assign p1_e_max = (exp_max >= FP_OFFSET) ? exp_max : FP_OFFSET;

    always_ff @(posedge clk) begin
        p1_fp_sgns <= fp_sgns;
        p1_fp_exps <= fp_exps;
        p1_fp_mans <= fp_mans;
    end


    logic                               p2_fp_sgns [BLOCK_DIM];
    logic [MXFP_SCALE_WIDTH - 1:0]      p2_sh_exp;
    logic unsigned [BLOCK_DIM-1:0][FP_EXP_WIDTH - 1 :0]     p2_m_shifts;
    logic unsigned [BLOCK_DIM-1:0][FP_MANT_WIDTH     :0]    p2_man_exts;
    logic [BLOCK_DIM-1:0] element_in_ready;
    logic                               p2_data_valid;
    logic  [BLOCK_DIM-1:0]              element_conv_valid, element_conv_ready;

    assign p2_sh_exp = p1_e_max - FP_OFFSET;

    for (genvar i=0; i<BLOCK_DIM; i++) begin
        assign p2_m_shifts[i]   = p1_e_max - p1_fp_exps[i];
        assign p2_fp_sgns[i]    = p1_fp_sgns[i];
        assign p2_man_exts[i]   = |p1_fp_exps[i] ? {1'b1, p1_fp_mans[i]} : {p1_fp_mans[i], 1'b0};  // Handling the denormalized fp numbers
    end

    logic [BLOCK_DIM - 1 : 0][MX_FP_MANT_WIDTH + MX_FP_EXP_WIDTH - 1:0] p2_elems;
    generate;
        for(genvar i=0; i<BLOCK_DIM; i++) begin : gen_mxfp_element
            fix_with_shift_2_fp # (
                .FIXED_DATA_WIDTH   (FP_MANT_WIDTH + 1),
                .FP_EXP_WIDTH       (MX_FP_EXP_WIDTH),
                .FP_MANT_WIDTH      (MX_FP_MANT_WIDTH),
                .SHIFT_WIDTH        (FP_EXP_WIDTH)
            ) mxfp_element_gen (
                .data_in    (p2_man_exts[i]),
                .shift_in   (p2_m_shifts[i]),
                .exp_out    (p2_elems[i][MX_FP_MANT_WIDTH + MX_FP_EXP_WIDTH - 1 : MX_FP_MANT_WIDTH]),
                .mant_out   (p2_elems[i][MX_FP_MANT_WIDTH - 1 : 0])
            );

            skid_buffer #(
                .DATA_WIDTH(MX_FP_MANT_WIDTH + MX_FP_EXP_WIDTH + 1)
            ) element_data (
                .clk           (clk),
                .rst           (rst),                        // Inverted reset
                .data_in       ({p2_fp_sgns[i], p2_elems[i]}),                      // flattened LEVEL_OUT_DIM * LEVEL_OUT_WIDTH
                .data_in_valid (p2_data_valid),
                .data_in_ready (element_in_ready[i]),                            // No sequential operation beforehand, hence ignored.
                .data_out      (element_data_out[i]),
                .data_out_valid(element_conv_valid[i]),
                .data_out_ready(element_conv_ready[i])
            );
        end
        
        assign data_in_ready = &element_in_ready;

        join_n #(
            .NUM_HANDSHAKES(BLOCK_DIM)
        ) join_data (
            .data_in_valid(element_conv_valid),
            .data_in_ready(element_conv_ready),
            .data_out_valid(mx_fp_data_out_valid),
            .data_out_ready(mx_fp_data_out_ready)
        );

    endgenerate

    
    always_ff @(posedge clk) begin
        scale_data_out  <=  p2_sh_exp + MXFP_SCALE_OFFSET;
        p2_data_valid   <=  data_in_valid;
    end
    
endmodule