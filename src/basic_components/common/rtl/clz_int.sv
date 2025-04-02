`timescale 1ns / 1ps

/*
Module      : Count of Leading Zeros (CLZ) in a Binary Number
Timing      : Combinatorial Logic
Description : Computes the count of leading zeros (CLZ) in an input binary number.
Status      : Library
*/


module clz_int #(
    parameter   width_i = 8,
    localparam  width_o = $clog2(width_i+1)
)(
    input  logic [width_i-1:0] i_num,
    output logic [width_o-1:0] o_lz
);

    logic [width_o-1:0] num_lz;

    always_comb begin
        num_lz = 0;
        for(int i=1; i<=width_i; i++) begin
            if(i_num[width_i-i]) begin
                break;
            end else begin
                num_lz++;
            end
        end
    end

    assign o_lz = num_lz;

endmodule