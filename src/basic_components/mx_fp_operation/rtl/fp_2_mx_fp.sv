`timescale 1ns / 1ps

/*
Module      : Convertion Units Floating Point with Configurable Precision to MX-FP
Timing      : Sequential, Takes 2 cycle to compute the dot product
Description : 

            Pipeline Stage 1 : Extracting the maximum exponent from the input data
            Pipeline Stage 2 : Normalizing the input data and converting it to MX-FP format
*/


module fp_2_mx_fp #(
    parameter CONVERT_DIM = 8, 
    parameter IN_MAN_WIDTH = 3,
    parameter IN_EXP_WIDTH = 4,
    parameter MX_FP_MANT_WIDTH = 3,
    parameter MX_FP_EXP_WIDTH = 4,
    parameter MX_FP_SCALE_WIDTH = 8
)(
    input   logic clk,
    input   logic rst,
    input   logic [CONVERT_DIM-1:0][IN_MAN_WIDTH + IN_EXP_WIDTH : 0] data_in,
    input   logic data_in_valid,
    output  logic data_in_ready,

    output  logic [CONVERT_DIM-1:0][MX_FP_MANT_WIDTH + MX_FP_EXP_WIDTH : 0] element_data_out,
    output  logic [MX_FP_SCALE_WIDTH-1:0] scale_data_out,
    output  logic element_data_out_valid,
    input   logic element_data_out_ready
);

    localparam MIN_FP_SCALE = 1 << (MX_FP_SCALE_WIDTH-1);


    // Split input into sgn, exp, man fields.
    logic                               fp_sgns [CONVERT_DIM];
    logic unsigned [IN_EXP_WIDTH - 1:0] fp_exps [CONVERT_DIM];
    logic unsigned [IN_EXP_WIDTH - 1:0] exp_max [CONVERT_DIM];
    logic unsigned [IN_MAN_WIDTH - 1:0] fp_mans [CONVERT_DIM];


    always_comb begin
        for (int i=0; i<CONVERT_DIM; i++) begin
            fp_sgns[i] = data_in[i][IN_EXP_WIDTH + IN_MAN_WIDTH];
            fp_exps[i] = data_in[i][IN_EXP_WIDTH + IN_MAN_WIDTH - 1 : IN_MAN_WIDTH];
            fp_mans[i] = data_in[i][IN_MAN_WIDTH-1:0];
        end
    end

    unsigned_max #(
        .width(IN_MAN_WIDTH),
        .length(CONVERT_DIM),
        .flop_output(0)
    ) u0_exp_max (
        .clk(clk),
        .input_data(fp_exps),
        .max_val(exp_max)
    );
    
    logic unsigned [MX_FP_SCALE_WIDTH - 1:0] p1_e_max;
    logic                               p1_fp_sgns [CONVERT_DIM];
    logic unsigned [IN_EXP_WIDTH - 1:0] p1_fp_exps [CONVERT_DIM];
    logic unsigned [IN_MAN_WIDTH - 1:0] p1_fp_mans [CONVERT_DIM];

    assign p1_e_max = (exp_max >= MIN_FP_SCALE) ? exp_max : MIN_FP_SCALE;

    always_ff @(posedge clk) begin
        p1_fp_sgns <= fp_sgns;
        p1_fp_exps <= fp_exps;
        p1_fp_mans <= fp_mans;
    end


    logic                               p2_fp_sgns [CONVERT_DIM];
    logic [MX_FP_SCALE_WIDTH - 1:0]     p2_e_max, p2_sh_exp;
    // logic [8:0] p2_sh_exp; TODO
    logic unsigned [IN_EXP_WIDTH - 1:0] p2_m_shifts [CONVERT_DIM];
    logic unsigned [IN_MAN_WIDTH - 1:0] p2_man_exts [CONVERT_DIM];

    logic                               p2_data_valid;

    assign p2_e_max  = p1_e_max;
    assign p2_sh_exp = p1_e_max - MIN_FP_SCALE;

    for (genvar i=0; i<CONVERT_DIM; i++) begin
        assign p2_m_shifts[i] = p1_e_max - p1_fp_exps[i];
        assign p2_fp_sgns[i] = p1_fp_sgns[i];
        assign p2_man_exts[i] = |p1_fp_exps[i] ? {1'b1, p1_fp_mans[i]} : {p1_fp_mans[i], 1'b0};  // Handling the denormalized fp numbers
    end

    logic [CONVERT_DIM -1 : 0][MX_FP_MANT_WIDTH + MX_FP_MANT_WIDTH - 1:0] p2_elems;

    for(genvar i=0; i<CONVERT_DIM; i++) begin
        mant_2_fp # (
            .FIXED_DATA_WIDTH(IN_MAN_WIDTH),
            .FP_EXP_WIDTH(MX_FP_EXP_WIDTH),
            .FP_MANT_WIDTH(MX_FP_MANT_WIDTH),
            .SHIFT_WIDTH(8)
        ) u0_fp_rnd (
            .i_num(p2_man_exts[i]),
            .i_shift(p2_m_shifts[i]),
            .o_exp(p2_elems[i][man_width+exp_width-1:man_width]),
            .o_man(p2_elems[i][man_width-1:0])
        );
    end

    skid_buffer #(
        .DATA_WIDTH(CONVERT_DIM * (MX_FP_MANT_WIDTH + MX_FP_EXP_WIDTH + 1))
    ) element_data (
        .clk           (clk),
        .rst           (!rst),                        // Inverted reset
        .data_in       ({p2_fp_sgns[i], p2_elems[i]}),                      // flattened LEVEL_OUT_DIM * LEVEL_OUT_WIDTH
        .data_in_valid (p2_data_valid),
        .data_in_ready (data_in_ready),
        .data_out      (element_data_out),
        .data_out_valid(element_data_out_valid),
        .data_out_ready(element_data_out_ready)
    );

    always_ff @(posedge clk) begin
        scale_data_out <= (p2_e_max == 8'hff) ? 8'hff : p2_sh_exp;
        p2_data_valid <= data_in_valid;
    end
    
endmodule