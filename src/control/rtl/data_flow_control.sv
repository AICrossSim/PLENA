`timescale 1ns / 1ps
`include "operation.svh"
`include "precision.svh"
`include "configuration.svh"
/*
Module      : Data Flow Control
Timing      : Sequential, 1 cycle to make the decision
Description : This module serves as the controller for all the memory related operations in the coprocessor,
            : controlling matrix sram, scratch sram, scalar sram and HBM interface.
            : It will record the states of the memory, checking whether it is currently busy or not, provide feedback to pipeline control unit.
            : It also controls iterative load process.
TODO: Failed load/write assertions, remove m_write_en and v_write_en
*/

module data_flow_control import precision_pkg::*; #(
    parameter   OPERAND_WIDTH           = 5,
    parameter   VLEN                    = 8,       
    parameter   MLEN                    = 8,
    parameter   Parallel_Rd_Dim         = 4       // Number of inputs per cycle
) (

    input       logic clk,
    input       logic rst,

    // Current Execution
    input       OP_BUNDLE                           assigned_op_bundle,

    input       logic [FIXED_DATA_WIDTH - 1 : 0] fixed_addr_1,
    input       logic [FIXED_DATA_WIDTH - 1 : 0] fixed_addr_2,
    input       logic [FIXED_DATA_WIDTH - 1 : 0] m_offset_addr,

    input       logic [FIXED_DATA_WIDTH - 1 : 0] v_waddr,
    input       logic v_write_en,
    input       logic [FIXED_DATA_WIDTH - 1 : 0] m_waddr,
    input       logic m_write_en,

    output      MEM_STALL_TYPE stall_req,

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
    output      logic [VLEN-1:0]                    s_sram_mask_b,

    // Interface with HBM
    output      logic [FIXED_DATA_WIDTH - 1 : 0] hbm_offset_addr,
    input       logic dma_m_ready,
    input       logic dma_v_ready,

    // Execution Control
    output      OP_BUNDLE          exe_op_bundle
);

localparam BITWIDTH_PER_ROW =  (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) * MLEN * Parallel_Rd_Dim / 8;
logic             exe_m_write_en, exe_v_write_en; 


always_ff @(posedge clk or negedge rst ) begin
    exe_op_bundle          <= assigned_op_bundle;
end


// Stall Request
logic previous_dma_m_ready;
logic previous_dma_v_ready;
always_ff @(posedge clk or negedge rst) begin
    if (rst) begin
        previous_dma_m_ready <= 1'b0;
        previous_dma_v_ready <= 1'b0;
    end else begin
        previous_dma_m_ready <= dma_m_ready;
        previous_dma_v_ready <= dma_v_ready;
    end
end

always_comb begin
    stall_req.stall_m_sram = ((dma_m_ready == 1'b1) & (previous_dma_m_ready == 1'b0)) ? 1'b1 : 1'b0;
    stall_req.stall_s_sram = ((dma_v_ready == 1'b1) & (previous_dma_v_ready == 1'b0)) ? 1'b1 : 1'b0;
    stall_req.stall_s_reg = 1'b0;
end




// Matrix SRAM Control
localparam MATRIX_LOAD_ITERATION = MLEN / Parallel_Rd_Dim;
localparam MATRIX_COUNTER_WIDTH = $clog2(MATRIX_LOAD_ITERATION);
logic [MATRIX_COUNTER_WIDTH - 1 : 0]    m_sram_counter;
logic               m_load_failed;
M_OP                track_m_op;

// Update addr only when the exe operation is MV or MV_O
always_comb begin
    if (exe_op_bundle.m_op == MV || exe_op_bundle.m_op == MV_O) begin
        m_sram_addr = fixed_addr_2;
    end else if (exe_op_bundle.stall_for_memory.stall_m_sram == 1'b1 && dma_m_ready) begin
        m_sram_addr = recorded_m_prefetch_addr;
    end
    if (record_m_prefetch_addr_en) begin
        recorded_m_prefetch_addr = fixed_addr_2;
    end
end

logic record_m_prefetch_addr_en;
logic [FIXED_DATA_WIDTH - 1 : 0] recorded_m_prefetch_addr;

always_ff @(posedge clk or negedge rst) begin
    if (rst) begin
        m_sram_counter <= 'b0;
        track_m_op <= STALL_M;
        m_sram_req <= 1'b0;
        m_sram_wen <= 1'b0;

    end else begin
        exe_m_write_en <= m_write_en;
        exe_v_write_en <= v_write_en;

        if (assigned_op_bundle.m_op == MV || assigned_op_bundle.m_op == MV_O) begin
            // Fetching the data from the Matrix Sram to the Matrix Machine
            // m_sram_busy <= 1'b1;
            m_sram_req      <= 1'b1;
            m_sram_transposed_read <= assigned_op_bundle.m_transposed_read;
        end
        
        // Wait for Testing MV_O
        // else if (m_sram_busy && m_m_ready) begin
        //     if (m_sram_counter == MATRIX_LOAD_ITERATION - 1) begin
        //         // m_sram_busy <= 1'b0;
        //         m_sram_counter <= 'b0;
        //         m_m_valid <= 1'b0;
                
        //     end else begin
        //         m_sram_counter <= m_sram_counter + 1'b1;
        //         m_m_valid <= 1'b1;
        //         m_v_valid <= 1'b1;
        //         m_o_valid <= (track_m_op == MV_O) ? 1'b1 : 1'b0;
        //     end

        // end 
        
        else if (assigned_op_bundle.stall_for_memory.stall_m_sram == 1'b1 && dma_m_ready) begin
            m_sram_req <= 1'b1;
            m_sram_wen <= 1'b1;
        end else begin
            m_sram_req <= 1'b0;
            m_sram_wen <= 1'b0;
        end


        if (assigned_op_bundle.h_op == PREFETCH_M) begin
            record_m_prefetch_addr_en <= 1'b1;
        end else begin
            record_m_prefetch_addr_en <= 1'b0;
        end

        // if (!m_sram_busy) begin
        //     track_m_op <= assigned_op_bundle.m_op;
        // end

        // if (m_sram_busy && !m_m_ready) begin
        //     m_load_failed <= 1'b1;
        // end else if (m_sram_busy && m_m_ready) begin
        //     m_load_failed <= 1'b0;
        // end
    end
end

// Vector SRAM Control
// Assuming the read cycle is 1 cycle for both ports.
assign s_sram_addr_a = (exe_op_bundle.m_op == MV_O) ?  m_offset_addr :
                                     exe_v_write_en ?  m_waddr : fixed_addr_1;

assign s_sram_addr_b = exe_m_write_en ? v_waddr : fixed_addr_2;

logic s_sram_load_failed;
always_ff @(posedge clk or negedge rst) begin
    if (rst) begin
        v_v_a_valid     <= 1'b0;
        v_v_b_valid     <= 1'b0;
    end else begin
        // Scratchpad SRAM Port A Control
        if(assigned_op_bundle.m_op != STALL_M || assigned_op_bundle.v_ele_op != STALL_V_ELEMENT || assigned_op_bundle.v_reduct_op != STALL_V_REDUCT) begin
            // Read Vector from SRAM
            v_v_a_valid     <= 1'b1;
            s_sram_req_a    <= 1'b1;
            s_sram_wen_a    <= 1'b0;

        end else if (assigned_op_bundle.stall_for_memory.stall_s_sram == 1'b1 && m_write_en && m_out_valid) begin
            // Write the result from matrix machine to the s_sram
            m_out_ready     <= 1'b1;
            s_sram_req_a    <= 1'b1;
            s_sram_wen_a    <= 1'b1;
        end else begin
            // No Scratchpad SRAM access request.
            v_v_a_valid     <= 1'b0;
            s_sram_req_a    <= 1'b0;
            s_sram_wen_a    <= 1'b0;
        end

        // Scratchpad Port B Control 
        if (assigned_op_bundle.m_op == MV_O || ((assigned_op_bundle.v_ele_op != STALL_V_ELEMENT) && !assigned_op_bundle.v_broadcast_en)) begin
            // Read Port activated
            v_v_b_valid     <= 1'b1;
            s_sram_req_b    <= 1'b1;
            s_sram_wen_b    <= 1'b0;
        end else if (v_write_en && v_v_out_valid) begin
            // Write Port activated
            v_v_out_ready   <= 1'b1;
            s_sram_req_b    <= 1'b1;
            s_sram_wen_b    <= 1'b1;
        end else if (assigned_op_bundle.stall_for_memory.stall_s_reg && dma_v_ready) begin
            // HBM Fetch to the scratchpad sram
            s_sram_wen_b    <= 1'b1;
            s_sram_req_b    <= 1'b1;
        end

        else begin
            // No SRAM access
            s_sram_req_b    <= 1'b0;
            v_v_b_valid     <= 1'b0;
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

