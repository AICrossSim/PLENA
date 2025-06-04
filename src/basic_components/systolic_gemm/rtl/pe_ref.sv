`timescale 1ns / 1ps

/*
Module      : Processing Element (PE) in Systolic GEMM
Timing      : Combinatorial
Description : This module is used to schedule the data prefetched from HBM to Matrix SRAM and Scratchpad SRAM.
            : It also shdules the write process from the two SRAMs to HBM.
            ： When the prefetch data is ready, it will outputs to the pipeline control to decide when to pass the data to the sram.
Status      : Under Development
*/



module P_Element(
    output reg  [31:0]  OUT,
    output      [31:0]  OUT_BOTTOM,
    output      [31:0]  OUT_RIGHT,
    input       [31:0]  IN_TOP,
    input       [31:0]  IN_LEFT,
    input               CLK,            // Positive Edge Triggered
    input               RST_N           // Negative Edge Triggered
);

// ==============================================================================================
// Declaration : registers, wires
// ==============================================================================================
    reg     [31:0]  REG_TOP;        // To store input from top of PE
    reg     [31:0]  REG_LEFT;       // To store input from left of PE
    reg     [31:0]  REG_MUL;        // To store the product of REG_TOP, REG_LEFT
    reg     [31:0]  REG_ADD;        // To store the sum of product, OUT
    reg     [31:0]  PRE_ADD;        // Give the correct operand for Adder, depend by CUR_STATE
    wire    [31:0]  RESULT_MUL;     
    wire    [31:0]  RESULT_ADD;
    wire            RESULT_isZero;

// ==============================================================================================
// STAGE 1: Store input to REG_TOP, REG_LEFT
// ==============================================================================================
    always @(posedge CLK or ~RST_N) begin
        if (RST_N == 1'b0) begin
            REG_TOP     <= `FPZero;
            REG_LEFT    <= `FPZero;
        end
        else begin
            REG_TOP     <= IN_TOP;
            REG_LEFT    <= IN_LEFT;
        end
    end
    assign OUT_BOTTOM   = REG_TOP;
    assign OUT_RIGHT    = REG_LEFT;

// ==============================================================================================
// STAGE 2: REG_TOP * REG_LEFT, result stores in pipeline register (REG_MUL)
// ==============================================================================================
    FP_Multiplier MUL(
        REG_TOP, REG_LEFT, RESULT_MUL
    );
    always @(posedge CLK or ~RST_N) begin 
        if (RST_N == 1'b0) begin
            REG_MUL     <= `FPZero;
        end
        else if (~(|REG_TOP) | ~(|REG_LEFT))
            REG_MUL     <= `FPZero;
        else
            REG_MUL     <= RESULT_MUL;
    end

// ==============================================================================================
// STAGE 3: OUT + REG_MUL , result stores in pipeline register (REG_ADD)
//      BUT data hazard occurs between stage 3, 4.
//      Therefore, adding a forwarding path instead passing `OUT` directly
// Forwarding Path:
//      Store the previous sum in register (PRE_ADD), then add it with REG_MUL  
// ==============================================================================================
    FP_Adder_Subtractor32 ADD(
        .Out(RESULT_ADD),       .isZero(RESULT_isZero),
        .A(REG_MUL),                .B(PRE_ADD)
    );
    always @(posedge CLK or ~RST_N) begin
        if (RST_N == 1'b0) begin
            REG_ADD     <= `FPZero;
            PRE_ADD     <= `FPZero;
        end
        // (OUT == 0 && REG_MUL == 0) or (A + B == 0)
        else if ((~(|PRE_ADD) & ~(|REG_MUL )) | RESULT_isZero) begin
            REG_ADD     <= `FPZero;
            PRE_ADD     <= `FPZero;
        end
        // OUT == 0
        else if (~|PRE_ADD) begin
            REG_ADD     <= REG_MUL ;
            PRE_ADD     <= REG_MUL ;
        end
        // REG_MUL == 0
        else if (~|REG_MUL ) begin
            REG_ADD     <= PRE_ADD;
            PRE_ADD     <= PRE_ADD;
        end
        else begin
            REG_ADD     <= RESULT_ADD;
            PRE_ADD     <= RESULT_ADD;
        end
    end

// ==============================================================================================
// STAGE 4: REG_ADD  -> OUT
// ==============================================================================================
    always @(posedge CLK or ~RST_N) begin
        if (RST_N == 1'b0) begin
            OUT         <= `FPZero; 
        end
        else begin
            OUT         <= REG_ADD ;
        end
    end

endmodule
