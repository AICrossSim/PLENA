
/*
Module      : data_concatenator
Description : 
*/

`timescale 1ns / 1ps

module data_concatenator #(
    parameter int Parallel_Rd_Dim = 4,                              // Number of inputs per cycle
    parameter int Datawidth = 8,                                    // Width of each input
    parameter int Overall_Rd_Dim = 12,                   
    localparam Cycles_To_Collect = Overall_Rd_Dim / Parallel_Rd_Dim // Number of cycles to collect
)(
    input  logic                         clk,                                   // Clock
    input  logic                         rst_n,                                 // Active-low reset
    input  logic [Parallel_Rd_Dim-1:0]  [Datawidth-1:0] data_in,                // Input data per cycle
    input  logic                         valid_in,                              // Input valid signal
    output logic                         ready,                                 // Ready to accept data
    output logic [Overall_Rd_Dim-1:0]   [Datawidth-1:0] data_out,               // Packed output array
    output logic                         valid_out                              // Output valid signal
);

    logic [Overall_Rd_Dim-1:0][Datawidth-1:0] buffer; // Buffer for concatenation
    int count; // Counter to track received sets

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            buffer <= 'b0;
            count  <= 0;
            valid_out <= 0;
        end else if (valid_in && ready) begin
            buffer <= {buffer[(Overall_Rd_Dim - Parallel_Rd_Dim)-1:0], data_in}; // Shift and insert new data
            count <= count + 1;

            if (count == Overall_Rd_Dim-1) begin
                data_out <= buffer; // Output when full
                valid_out <= 1;
                count <= 0; // Reset counter
            end else begin
                valid_out <= 0;
            end
        end
    end

    assign ready = (count < Overall_Rd_Dim); // Ready to accept data unless full

endmodule
