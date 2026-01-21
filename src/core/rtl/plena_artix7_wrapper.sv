`timescale 1ns / 1ps

`include "global_define.vh"
`include "precision.svh"
`include "configuration.svh"
`include "operation.svh"
`include "tl_util.svh"

/*
Module      : Plena Artix-7 Test Wrapper
Description : Wrapper for plena that terminates HBM TileLink interfaces internally
              for synthesis testing on Artix-7 (which doesn't have HBM).
              This allows measuring core logic resource usage without I/O overhead.
*/

module plena_artix7_wrapper import configuration_pkg::*; import instruction_pkg::*; #(
    `ifdef SIMULATION
        parameter string FP_MEM_INIT_FILE       = "",
        parameter string INT_MEM_INIT_FILE      = "",
        parameter string V_SRAM_RESULT_FILE     = "",
        parameter string HBM_ADDR_MAPPER_FILE   = "",
        parameter string HBM_STRIDE_INIT_FILE   = ""
    `endif
)(
    input   logic clk,
    input   logic rst,
    // Minimal external interface for testing
    input   logic [INSTRUCTION_LENGTH - 1 : 0] instruction,
    input   logic instruction_valid,
    output  logic instruction_ready,
    output  logic system_break
);

    // Internal TileLink connections (not exposed as I/O)
    `TL_DECLARE(HBM_ELE_WIDTH,   HBM_ADDR_WIDTH, SourceWidth, SinkWidth, m_element);
    `TL_DECLARE(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, m_scale);
    `TL_DECLARE(HBM_ELE_WIDTH,   HBM_ADDR_WIDTH, SourceWidth, SinkWidth, v_element);
    `TL_DECLARE(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, v_scale);

    // Instantiate the core plena module
    // DONT_TOUCH prevents optimization of internal memories during synthesis
    (* DONT_TOUCH = "TRUE" *)
    plena #(
        `ifdef SIMULATION
            .FP_MEM_INIT_FILE(FP_MEM_INIT_FILE),
            .INT_MEM_INIT_FILE(INT_MEM_INIT_FILE),
            .V_SRAM_RESULT_FILE(V_SRAM_RESULT_FILE),
            .HBM_ADDR_MAPPER_FILE(HBM_ADDR_MAPPER_FILE),
            .HBM_STRIDE_INIT_FILE(HBM_STRIDE_INIT_FILE)
        `endif
    ) plena_core (
        .clk(clk),
        .rst(rst),
        .instruction(instruction),
        .instruction_valid(instruction_valid),
        .instruction_ready(instruction_ready),
        .system_break(system_break),
        // Connect internal TileLink signals
        `TL_FORWARD_HOST_PORT(m_out_element, m_element),
        `TL_FORWARD_HOST_PORT(m_out_scale,   m_scale),
        `TL_FORWARD_HOST_PORT(v_out_element, v_element),
        `TL_FORWARD_HOST_PORT(v_out_scale,   v_scale)
    );

    // Terminate TileLink interfaces with simple "always ready, never valid" logic
    // This prevents the logic from being optimized away while avoiding I/O explosion

    // Matrix Element Channel (m_element)
    assign m_element_a_ready = 1'b1;
    assign m_element_b_valid = 1'b0;
    assign m_element_b = '0;
    assign m_element_c_ready = 1'b1;
    assign m_element_d_valid = 1'b0;
    assign m_element_d = '0;
    assign m_element_e_ready = 1'b1;

    // Matrix Scale Channel (m_scale)
    assign m_scale_a_ready = 1'b1;
    assign m_scale_b_valid = 1'b0;
    assign m_scale_b = '0;
    assign m_scale_c_ready = 1'b1;
    assign m_scale_d_valid = 1'b0;
    assign m_scale_d = '0;
    assign m_scale_e_ready = 1'b1;

    // Vector Element Channel (v_element)
    assign v_element_a_ready = 1'b1;
    assign v_element_b_valid = 1'b0;
    assign v_element_b = '0;
    assign v_element_c_ready = 1'b1;
    assign v_element_d_valid = 1'b0;
    assign v_element_d = '0;
    assign v_element_e_ready = 1'b1;

    // Vector Scale Channel (v_scale)
    assign v_scale_a_ready = 1'b1;
    assign v_scale_b_valid = 1'b0;
    assign v_scale_b = '0;
    assign v_scale_c_ready = 1'b1;
    assign v_scale_d_valid = 1'b0;
    assign v_scale_d = '0;
    assign v_scale_e_ready = 1'b1;

endmodule
