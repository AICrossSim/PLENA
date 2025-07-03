`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Cache System for HBM Prefetching
Timing      : Combinatorial
Description : Due to the observation, it is noticeable that we always need a continuous range of data to do the computation
            : Hense, we use a cache system to store the prefetched data from HBM.

Status      : Under Development
*/

module simple_cache #(
    parameter int CACHE_SIZE = 1024, // Size of the cache in number of elements
    parameter int ELE_WIDTH = 64,     // Width of each element in bits
    parameter int SCALE_WIDTH = 32,   // Width of each scale in bits
) (
    input logic clk,
    input logic rst,
    input logic req,
    input logic [HBM_ADDR_WIDTH - 1: 0] rd_addr,    
    output logic [ELE_WIDTH - 1: 0] rd_element,      
    output logic [SCALE_WIDTH - 1: 0] rd_scale,
    output logic matched,
    input logic  wr_en,      
    input logic [HBM_ADDR_WIDTH - 1: 0] wr_addr,   
    input logic [ELE_WIDTH - 1: 0] wr_element, 
    input logic [SCALE_WIDTH - 1: 0] wr_scale
)

    // Cache memory
    logic [ELE_WIDTH - 1:0] cache_element [0:CACHE_SIZE-1];
    logic [SCALE_WIDTH - 1:0] cache_scale [0:CACHE_SIZE-1];
    logic [HBM_ADDR_WIDTH - 1:0] cache_addr [0:CACHE_SIZE-1];

    // Read operation
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            // Reset cache
            for (int i = 0; i < CACHE_SIZE; i++) begin
                cache_element[i] <= '0;
                cache_scale[i] <= '0;
                cache_addr[i] <= '0;
            end
        end else if (req) begin
            // Read from cache
            for (int i = 0; i < CACHE_SIZE; i++) begin
                if (cache_addr[i] == rd_addr) begin
                    rd_element <= cache_element[i];
                    rd_scale <= cache_scale[i];
                end
            end
        end else if (wr_en) begin
            // Write to cache
            for (int i = 0; i < CACHE_SIZE; i++) begin
                if (cache_addr[i] == wr_addr) begin
                    cache_element[i] <= wr_element;
                    cache_scale[i] <= wr_scale;
                end else if (cache_addr[i] == '0) begin // Find an empty slot
                    cache_addr[i] <= wr_addr;
                    cache_element[i] <= wr_element;
                    cache_scale[i] <= wr_scale;
                    break;
                end
            end
        end
    end




endmodule