`timescale 1ns / 1ps

/*
Module      : Assuming all Fixed-Point Data, Find the Maximum Value in an Array
Timing      : Combinatorial Logic
Description : 
*/


module mant_2_fp #(
    parameter FIXED_DATA_WIDTH      = 8,
    parameter FP_EXP_WIDTH          = 3,
    parameter FP_MANT_WIDTH         = 2,
    parameter SHIFT_WIDTH           = 8
)(
    input  logic signed         [FIXED_DATA_WIDTH-1:0]  data_in,
    input  logic unsigned       [SHIFT_WIDTH-1:0]       shift_in,
    output logic                [FP_EXP_WIDTH-1:0]      exp_out,
    output logic                [FP_MANT_WIDTH-1:0]     mant_out
);

    // Max exponent/mantissa values of element type.
    localparam MAX_EXP_ELEM = (1 << FP_EXP_WIDTH) - 1;
    localparam MAX_MAN_ELEM = (1 << FP_MANT_WIDTH) - 1;
    localparam RND_BITS = FIXED_DATA_WIDTH-FP_MANT_WIDTH;

    // Count leading zeros, align input.
    logic [$clog2(FIXED_DATA_WIDTH):0] lz_num;
    logic [FIXED_DATA_WIDTH-1:0] aligned_data;

    clz_int #(
        .width_i(FIXED_DATA_WIDTH)
    ) u_clz (
        .data_in(data_in),
        .o_lz(lz_num)
    );

    // Prepare data, removing the leading zeros.
    assign aligned_data = data_in << lz_num;

    // Handle non-denormal case. Round mantissa.
    logic R_nrm;
    logic S_nrm;
    logic p0_nrm_rnd;

    generate;
        if (RND_BITS > 1) begin : gen_R
            assign R_nrm = aligned_data[FIXED_DATA_WIDTH-FP_MANT_WIDTH-2];
        end
        else begin
            assign R_nrm = 1'b0;
        end


    endgenerate


    assign S_nrm = |aligned_data[FIXED_DATA_WIDTH-FP_MANT_WIDTH-3:0];
    assign p0_nrm_rnd = R_nrm && (aligned_data[FIXED_DATA_WIDTH-FP_MANT_WIDTH-1] || S_nrm);

    logic [FP_MANT_WIDTH:0] p0_man_nrm_ofl;  // Extra bit to check for overflow after rounding.
    logic [FP_MANT_WIDTH-1:0] p0_man_nrm;      // Output mantissa if output is not denormal.
    logic                   p0_exp_nrm_ofl;  // 1 if mantissa overflowed, 0 otherwise.

    assign p0_man_nrm_ofl = aligned_data[FIXED_DATA_WIDTH-2:FIXED_DATA_WIDTH-FP_MANT_WIDTH-1] + {{(FP_MANT_WIDTH-1){1'b0}}, p0_nrm_rnd};

    assign p0_exp_nrm_ofl = p0_man_nrm_ofl[FP_MANT_WIDTH];
    assign p0_man_nrm     = p0_man_nrm_ofl[FP_MANT_WIDTH-1:0];

    // Truncation necessary if exponent overflows.
    logic p0_truncate;

    assign p0_truncate = p0_exp_nrm_ofl && (shift_in == 0) && (lz_num == 0);

    // Handle denormal case. Round mantissa.
    logic [SHIFT_WIDTH+1:0] p0_dnm_shift; // Amount to shift by if output is denormal.
    logic [FIXED_DATA_WIDTH-2:0] sticky_mask;

    logic R_dnm;
    logic S_dnm;
    logic p0_dnm_rnd;

    assign p0_dnm_shift = $unsigned(shift_in) + $unsigned(lz_num) + $unsigned(FIXED_DATA_WIDTH) - $unsigned(MAX_EXP_ELEM) - $unsigned(FP_MANT_WIDTH);

    assign sticky_mask = ~({(FIXED_DATA_WIDTH-1){1'b1}} << (p0_dnm_shift-1));

    assign S_dnm = |(aligned_data[FIXED_DATA_WIDTH-2:0] & sticky_mask);

    always_comb begin
        if($signed({1'b0, shift_in}) <= $signed($unsigned(MAX_EXP_ELEM) + $unsigned(FP_MANT_WIDTH) - $unsigned(lz_num))) begin
            R_dnm = aligned_data[p0_dnm_shift - 1];
        end else begin
            R_dnm = 0;
        end

        if($signed({1'b0, shift_in}) < $signed($unsigned(MAX_EXP_ELEM) + $unsigned(FP_MANT_WIDTH) - $unsigned(lz_num))) begin
            p0_dnm_rnd = R_dnm && (aligned_data[p0_dnm_shift] || S_dnm);
        end else begin
            p0_dnm_rnd = R_dnm && S_dnm;
        end
    end

    logic [FP_MANT_WIDTH-1:0] p0_man_dnm_shifted;
    logic   [FP_MANT_WIDTH:0] p0_man_dnm_ofl;  // Extra bit to check for overflow after rounding.
    logic [FP_MANT_WIDTH-1:0] p0_man_dnm;      // Output mantissa if output is not denormal.
    logic                   p0_exp_dnm_ofl;  // 1 if mantissa overflowed, 0 otherwise.

    assign p0_man_dnm_shifted = aligned_data >> (p0_dnm_shift);

    assign p0_man_dnm_ofl = p0_man_dnm_shifted + {{(FP_MANT_WIDTH-1){1'b0}}, p0_dnm_rnd};

    assign p0_exp_dnm_ofl = p0_man_dnm_ofl[FP_MANT_WIDTH];
    assign p0_man_dnm = p0_man_dnm_ofl[FP_MANT_WIDTH-1:0];

    // Calculate output exponent, and whether output is denormal, not accounting for overflow.
    logic [SHIFT_WIDTH+1:0] p0_exp_out;
    logic                   p0_dnm_out;   // Is output denormal?

    assign p0_exp_out = $unsigned(MAX_EXP_ELEM) + $unsigned(p0_exp_nrm_ofl) - $unsigned(shift_in) - $unsigned(lz_num);
    assign p0_dnm_out = $signed($unsigned(MAX_EXP_ELEM) - $unsigned(lz_num)) <= $signed({1'b0, shift_in});


    // Assign outputs.
    always_comb begin
        if(data_in != 0) begin
            if(p0_dnm_out) begin
                exp_out = p0_exp_dnm_ofl;
            end else if(p0_truncate) begin
                exp_out = MAX_EXP_ELEM;
            end else begin
                exp_out = p0_exp_out;
            end

        end else begin
            exp_out = 0;
        end
    end

    always_comb begin
        if(p0_dnm_out) begin
            mant_out = p0_man_dnm;
        end else if(p0_truncate) begin
            mant_out = (data_in != 0) ? MAX_MAN_ELEM : 0;
        end else begin
            mant_out = p0_man_nrm;
        end
    end

endmodule
