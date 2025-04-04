`timescale 1ns / 1ps
/*
Module      : MX-FP Configurable Precision Unit Adder (With Sign)
Timing      : Combinatorial Logic
Description : Assuming the two MX-FP input data has different scaling, but with same scale and element data format.
Status      : Passed Simple Tests
TODO        : Do we need to asssume we shift towards max scale factor?
*/

module mx_fp_unit_adder #(
    parameter MXFP_EXP_WIDTH = 4,
    parameter MXFP_MANT_WIDTH = 3,
    parameter MXFP_SCALE_WIDTH = 8,
    // Amount of bits needed to shift mantissas for alignment
    parameter EXT_MANT_WIDTH = 0,
    // Need to increase exp width by 1 to handle overflow
    parameter EXT_EXP_WIDTH = 0
)(
    input  logic [MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] element_data_a,
    input  logic [MXFP_SCALE_WIDTH - 1 : 0]             scale_data_a,
    input  logic [MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] element_data_b,
    input  logic [MXFP_SCALE_WIDTH - 1 : 0]             scale_data_b,
    output logic [MXFP_EXP_WIDTH + EXT_EXP_WIDTH + MXFP_MANT_WIDTH + EXT_MANT_WIDTH : 0] element_data_out,
    output logic [MXFP_SCALE_WIDTH - 1 : 0]             scale_data_out
);


    logic [MXFP_SCALE_WIDTH - 1 : 0]    shift_scale, result_scale;
        
    logic [MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] shifted_element_data_a, shifted_element_data_b;

    always_comb begin
        if (scale_data_a > scale_data_b) begin
            shift_scale            = scale_data_a - scale_data_b;
            shifted_element_data_a = element_data_a;
            shifted_element_data_b = {  
                                        element_data_b[MXFP_EXP_WIDTH + MXFP_MANT_WIDTH], 
                                        element_data_b[MXFP_EXP_WIDTH + MXFP_MANT_WIDTH - 1 : MXFP_MANT_WIDTH] + shift_scale[MXFP_EXP_WIDTH - 1: 0], 
                                        element_data_b[MXFP_MANT_WIDTH - 1 : 0] 
                                      };
            result_scale = scale_data_a;
        end
        else begin
            shift_scale            = scale_data_b - scale_data_a;
            shifted_element_data_a = {  
                                        element_data_a[MXFP_EXP_WIDTH + MXFP_MANT_WIDTH],
                                        element_data_a[MXFP_EXP_WIDTH + MXFP_MANT_WIDTH - 1 : MXFP_MANT_WIDTH] + shift_scale[MXFP_EXP_WIDTH - 1: 0],
                                        element_data_a[MXFP_MANT_WIDTH - 1 : 0] 
                                      };
            shifted_element_data_b = element_data_b;
            result_scale = scale_data_a;
        end
    end

    fp_cp_adder #(
        .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
        .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
        .EXT_MANT_WIDTH(EXT_MANT_WIDTH),
        .EXT_EXP_WIDTH(EXT_EXP_WIDTH)
    )   element_addition (
        .data_a(shifted_element_data_a),
        .data_b(shifted_element_data_b),
        .data_out(element_data_out)
    );
    assign scale_data_out = result_scale;



endmodule