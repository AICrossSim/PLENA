`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Memory Control
Timing      : Combinatorial
Description : This module serves as the controller for all the memory related operations in the coprocessor,
            : controlling matrix sram, scratch sram, scalar sram and HBM interface.
            : It will record the states of the memory, checking whether it is currently busy or not, provide feedback to pipeline control unit.
*/

module data_flow_control #(
    parameter   OPERAND_WIDTH           = 5,
    parameter   FIXED_DATA_WIDTH        = 32,
    parameter   VLEN                    = 8,       
    parameter   MLEN                    = 8,
    parameter   Parallel_Rd_Dim         = 4       // Number of inputs per cycle
) (

    input       logic clk,
    input       logic rst,

    // Current Execution
    input       M_OP                cur_m_op,
    input       logic               cur_m_transposed_read,
    input       V_ELEMENT_OP        cur_v_ele_op,
    input       logic               cur_v_broadcast_en,
    input       V_REDUCT_OP         cur_v_reduct_op,
    input       S_FP_OP             cur_s_fp_op,
    input       S_FIXED_OP          cur_s_fixed_op,

    input       logic [FIXED_DATA_WIDTH - 1 : 0] loaded_rs1,
    input       logic [FIXED_DATA_WIDTH - 1 : 0] loaded_rs2,

    input       logic [FIXED_DATA_WIDTH - 1 : 0] vector_waddr,

    output      logic load_process_failed,

    // Interface with Matrix Machine
    input       logic m_m_ready,
    output      logic m_m_valid,

    output      logic m_v_valid,
    input       logic m_v_ready,

    output      logic m_o_valid,
    input       logic m_o_ready,

    input       logic m_out_valid,
    output      logic m_out_ready,

    // Interface with Matrix SRAM
    output      logic [FIXED_DATA_WIDTH - 1 : 0] m_sram_addr,
    output      logic m_sram_wen,
    output      logic m_sram_req,
    output      logic m_sram_transposed_read,
    output      logic m_sram_busy,

    // Interface with Vector Machine
    output      logic v_v_a_valid,
    input       logic v_v_a_ready,

    output      logic v_v_b_valid,
    input       logic v_v_b_ready,

    input       logic v_v_out_valid,
    output      logic v_v_out_ready,

    output      logic v_s_in_valid,
    input       logic v_s_in_ready,
    input       logic v_s_out_valid,
    output      logic v_s_out_ready,

    // Interface with Scratchpad SRAM
    output      logic s_sram_req_a,
    output      logic s_sram_wen_a,
    output      logic [FIXED_DATA_WIDTH - 1 : 0]    s_sram_addr_a,
    output      logic [VLEN-1:0]                    s_sram_mask_a,

    output      logic s_sram_req_b,
    output      logic s_sram_wen_b,
    output      logic [FIXED_DATA_WIDTH - 1 : 0]    s_sram_addr_b,
    output      logic [VLEN-1:0]                    s_sram_mask_b
);


// -----------------
M_OP                exe_m_op;
logic               exe_m_transposed_read;
V_ELEMENT_OP        exe_v_ele_op;
logic               exe_v_broadcast_en;
V_REDUCT_OP         exe_v_reduct_op;
S_FP_OP             exe_s_fp_op;
S_FIXED_OP          exe_s_fixed_op;


always_ff @(posedge clk or negedge rst ) begin
    if (rst) begin
        exe_m_op               <= STALL_M;
        exe_m_transposed_read  <= 1'b0;
        exe_v_ele_op           <= STALL_V_ELEMENT;
        exe_v_broadcast_en     <= 1'b0;
        exe_v_reduct_op        <= STALL_V_REDUCT;
        exe_s_fp_op            <= STALL_S_FP;
        exe_s_fixed_op         <= STALL_S_FIXED;
    end else begin
        exe_m_op               <= cur_m_op;
        exe_m_transposed_read  <= cur_m_transposed_read;
        exe_v_ele_op           <= cur_v_ele_op;
        exe_v_broadcast_en     <= cur_v_broadcast_en;
        exe_v_reduct_op        <= cur_v_reduct_op;
        exe_s_fp_op            <= cur_s_fp_op;
        exe_s_fixed_op         <= cur_s_fixed_op;
    end
end


// Load Process Stall
assign load_process_failed = m_load_failed || s_sram_load_failed;

// Matrix SRAM Control
localparam MATRIX_LOAD_ITERATION = MLEN / Parallel_Rd_Dim;
localparam MATRIX_COUNTER_WIDTH = $clog2(MATRIX_LOAD_ITERATION);
logic [MATRIX_COUNTER_WIDTH - 1 : 0]    m_sram_counter;
logic [FIXED_DATA_WIDTH-1:0]            next_m_sram_addr;
logic m_load_failed;
M_OP                track_m_op;

// Update addr only when the exe operation is MV or MV_O
always_comb begin
    next_m_sram_addr = m_sram_addr; // hold current value by default
    if (exe_m_op == MV || exe_m_op == MV_O) begin
        next_m_sram_addr = loaded_rs2;
    end
end
assign m_sram_addr = next_m_sram_addr;

always_ff @(posedge clk or negedge rst) begin
    if (rst) begin
        m_sram_busy <= 1'b0;
        m_sram_counter <= 'b0;
        track_m_op <= STALL_M;
    end else begin
        if (cur_m_op == MV || cur_m_op == MV_O) begin
            m_sram_busy <= 1'b1;
            m_sram_counter <= 'b0;
            m_sram_req  <= 1'b1;
            m_sram_transposed_read <= cur_m_transposed_read;

        end else if (m_sram_busy && m_m_ready) begin
            if (m_sram_counter == MATRIX_LOAD_ITERATION - 1) begin
                m_sram_busy <= 1'b0;
                m_sram_counter <= 'b0;
                m_m_valid <= 1'b0;
                
            end else begin
                m_sram_counter <= m_sram_counter + 1'b1;
                m_m_valid <= 1'b1;
                m_v_valid <= 1'b1;
                m_o_valid <= (track_m_op == MV_O) ? 1'b1 : 1'b0;
            end
        end

        if (!m_sram_busy) begin
            track_m_op <= cur_m_op;
        end

        if (m_sram_busy && !m_m_ready) begin
            m_load_failed <= 1'b1;
        end else if (m_sram_busy && m_m_ready) begin
            m_load_failed <= 1'b0;
        end
    end
end

// Vector SRAM Control
// Assuming the read cycle is 1 cycle for both ports.
assign s_sram_addr_a = loaded_rs1;
assign s_sram_addr_b = loaded_rs2;

logic s_sram_load_failed;
always_ff @(posedge clk or negedge rst) begin
    if (rst) begin
        v_v_a_valid     <= 1'b0;
        v_v_b_valid     <= 1'b0;
    end else begin
        if(cur_m_op == MV || ((cur_v_ele_op != STALL_V_ELEMENT || cur_v_ele_op != MV_O) && cur_v_broadcast_en)) begin
            // Only Single Port a is required
            v_v_a_valid     <= 1'b1;
            v_v_b_valid     <= 1'b0;
            s_sram_req_a    <= 1'b1;
            s_sram_req_b    <= 1'b0;

        end else if (cur_m_op == MV_O || ((cur_v_ele_op != STALL_V_ELEMENT || cur_v_ele_op != MV_O) && !cur_v_broadcast_en)) begin
            // Two Ports are required
            v_v_a_valid     <= 1'b1;
            v_v_b_valid     <= 1'b1;
            s_sram_req_a    <= 1'b1;
            s_sram_req_b    <= 1'b1;
        end
        else begin
            // No SRAM access
            v_v_a_valid     <= 1'b0;
            v_v_b_valid     <= 1'b0;
            s_sram_req_a    <= 1'b0;
            s_sram_req_b    <= 1'b0;
        end
        // TODO: the check condition of the req signals from matrix machine and vector machine need to be revised.
        if ((s_sram_req_a || s_sram_req_b) && !(v_v_a_ready || v_v_b_ready || m_o_ready || m_v_ready)) begin
            s_sram_load_failed <= 1'b1;
        end else begin
            s_sram_load_failed <= 1'b0;
        end
    end

end
endmodule

