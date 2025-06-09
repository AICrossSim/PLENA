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
*/

module data_flow_control import precision_pkg::*;  #(
    parameter   OPERAND_WIDTH           = 5,
    parameter   VLEN                    = 8,       
    parameter   MLEN                    = 8,
    parameter   Parallel_Rd_Dim         = 4,       // Number of inputs per cycle
    localparam MATRIX_LOAD_ITERATION = MLEN,
    localparam BLOCK_NUM = VLEN / BLOCK_DIM
) (

    input       logic clk,
    input       logic rst,

    // Current Execution
    input       OP_BUNDLE                       exe_stage_op,
    input       MEM_WEN_INFO                    mem_write_control,
    output      MEM_WREQ_INFO write_req,

    // Status Tracking
    output      logic m_load_in_process,
    output      logic v_load_in_process,

    // Interface with Matrix Machine
    input       logic m_m_ready,
    output      logic m_m_valid,
    output      logic m_v_valid,
    input       logic m_v_ready,
    input       logic m_out_valid,
    output      logic m_out_ready,
    input       logic m_write_request,
    input       logic [FIXED_DATA_WIDTH - 1 : 0] m_write_addr,

    // Interface with Matrix SRAM
    output      logic [FIXED_DATA_WIDTH - 1 : 0] m_sram_raddr,
    output      logic [FIXED_DATA_WIDTH - 1 : 0] m_sram_waddr,
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

    input       logic v_write_request,
    input       logic [FIXED_DATA_WIDTH - 1 : 0] v_write_addr,

    // Interface with Vector SRAM
    output      logic v_sram_req_a,
    output      logic v_sram_wen_a,
    output      logic [FIXED_DATA_WIDTH - 1 : 0]    v_sram_addr_a,
    output      logic [VLEN-1:0]                    v_sram_mask_a,
    output      logic select_write_data_a,          

    output      logic v_sram_req_b,
    output      logic v_sram_wen_b,
    output      logic [FIXED_DATA_WIDTH - 1 : 0]    v_sram_addr_b,
    output      logic [VLEN-1:0]                    v_sram_mask_b,

    // Interface with HBM
    input       logic prefetch_m_valid,
    input       logic prefetch_v_valid,
    input       logic hbm_ready_to_write,
    output      logic hbm_write_data_valid,
    output      logic hbm_m_req_prefetch_data
);
    // Package Imports
    import pipeline_pkg::MAX_PIPELINE_STAGE;
    import configuration_pkg::*;

    localparam M_LD_COUNT_WIDTH = $clog2(MATRIX_LOAD_ITERATION);
    localparam M_PF_COUNT_WIDTH = $clog2(HBM_M_Prefetch_Amount);
    localparam V_PF_COUNT_WIDTH = $clog2(HBM_V_Prefetch_Amount);

    logic m_m_load_in_process, m_v_load_in_process;
    assign m_load_in_process = m_m_load_in_process | m_v_load_in_process;
    assign v_load_in_process = 1'b0;        // Currently not used, but can be extended for vector load in the future.

    // Memory Execution Control and Dependency Monitor
    localparam BYTES_PER_ROW =  (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) * MLEN * Parallel_Rd_Dim / 8;

    OP_BUNDLE  mem_stage_op;
    MEM_WEN_INFO mem_stage_write_control;

    always_ff @(posedge clk ) begin
        mem_stage_op          <= exe_stage_op;
        mem_stage_write_control <= mem_write_control;
    end

    assign v_sram_mask_a = {BLOCK_NUM{1'b1}};
    assign v_sram_mask_b = {BLOCK_NUM{1'b1}};

    // Stall Request
    logic previous_dma_m_ready;
    logic previous_dma_v_ready;
    always_ff @(posedge clk) begin
        if (rst) begin
            previous_dma_m_ready <= 1'b0;
            previous_dma_v_ready <= 1'b0;
        end else begin
            previous_dma_m_ready <= prefetch_m_valid;
            previous_dma_v_ready <= prefetch_v_valid;
        end
    end

    //Request Asserted in single cycle
    always_comb begin
        write_req.wreq_m_sram        = ((prefetch_m_valid == 1'b1) & (previous_dma_m_ready == 1'b0)) ? 1'b1 : 1'b0;
        write_req.wreq_s_sram_port_a = ((m_write_request == 1'b1) || (v_write_request == 1'b1)) ? 1'b1 : 1'b0;
        write_req.wreq_s_sram_port_b = ((prefetch_v_valid == 1'b1) & (previous_dma_v_ready == 1'b0)) ? 1'b1 : 1'b0;
    end


    logic [FIXED_DATA_WIDTH - 1 : 0] recorded_m_prefetch_addr, recorded_m_load_addr;
    
    // -----------------------------
    // Matrix SRAM
    // -----------------------------


    logic continuous_load_m_en, continuous_prefetch_m_en;
    logic [M_LD_COUNT_WIDTH : 0] m_sram_load_counter;
    logic [M_PF_COUNT_WIDTH : 0] m_sram_prefetch_counter;
    logic m_m_load, m_v_load;
    logic hbm_load_write_data;


    // Update addr only when the exe operation is MV or MV_O
    always_comb begin
        if (mem_stage_op.m_op == MV || mem_stage_op.m_op == MV_O || continuous_load_m_en) begin
            m_sram_raddr = recorded_m_load_addr + m_sram_load_counter * BYTES_PER_ROW;
        end else begin
            m_sram_raddr = 'b0;
        end
        
        if (continuous_prefetch_m_en) begin
            m_sram_waddr = recorded_m_prefetch_addr + (m_sram_prefetch_counter - 1) * BYTES_PER_ROW;
        end else begin
            m_sram_waddr = 'b0;
        end

        if (rst) begin
            recorded_m_prefetch_addr    = 'b0;
            recorded_m_load_addr        = 'b0;
        end else begin 
            if (exe_stage_op.h_op == PREFETCH_M) begin
                recorded_m_prefetch_addr = exe_stage_op.addr_2;
            end else if (m_sram_prefetch_counter == MATRIX_LOAD_ITERATION) begin

            end else if (exe_stage_op.m_op != STALL_M) begin
                recorded_m_load_addr = exe_stage_op.addr_2;
            end 
        end
    end

    // -----------------------------
    // Matrix SRAM
    // -----------------------------

    // Read  Port -> Matrix Weight Load
    // Write Port -> Matrix Weight Prefetch

    always_ff @(posedge clk) begin
        if (rst) begin
            m_sram_req <= 1'b0;
            hbm_m_req_prefetch_data <= 1'b0;
            continuous_load_m_en        <= 1'b0;
            continuous_prefetch_m_en    <= 1'b0;
            m_sram_load_counter         <= 'b0;
            m_sram_prefetch_counter     <= 'b0;
            m_m_load    <= 1'b0;
            m_m_valid   <= 1'b0;
            m_out_ready <= 1'b0;
            m_m_load_in_process <= 1'b0;
        end else begin
            m_out_ready <= 1'b1;
            m_m_valid   <= m_m_load;

            // Matrix SRAM Read Port Control
            if (exe_stage_op.m_op != STALL_M) begin
                m_sram_req      <= 1'b1;
                m_m_load        <= 1'b1;
                m_sram_transposed_read <= exe_stage_op.m_transposed_read;
                m_sram_load_counter <= 'b0;
                continuous_load_m_en <= 1'b1;
                m_m_load_in_process <= 1'b1;
            end else if (continuous_load_m_en & m_m_ready) begin
                if (m_sram_load_counter == MATRIX_LOAD_ITERATION - 1) begin
                    m_sram_req <= 1'b0;
                    m_m_load   <= 1'b0;
                    m_sram_load_counter <= 'b0;
                    continuous_load_m_en <= 1'b0;
                    m_m_load_in_process <= 1'b0;
                end else begin
                    m_m_load    <= 1'b1;
                    m_sram_req  <= 1'b1;
                    m_sram_load_counter <= m_sram_load_counter + 1'b1;
                    m_m_load_in_process <= 1'b1;
                end
            end else begin
                m_m_load   <= 1'b0;
                m_sram_req <= 1'b0;
                hbm_m_req_prefetch_data <= 1'b0;
                continuous_load_m_en <= 1'b0;
            end

            // Matrix SRAM Write Port Control
            if (mem_write_control.w_m_sram_en == 1'b1 && prefetch_m_valid) begin
                // Prefetching the data from the HBM to the Matrix Sram
                hbm_m_req_prefetch_data <= 1'b1;
                continuous_prefetch_m_en <= 1'b1;
                m_sram_prefetch_counter <= m_sram_prefetch_counter + 1'b1;
            end else if (continuous_prefetch_m_en & m_sram_prefetch_counter < HBM_M_Prefetch_Amount & m_sram_wen) begin
                hbm_m_req_prefetch_data <= 1'b1;
                m_sram_prefetch_counter <= m_sram_prefetch_counter + 'b1;
            end else if (m_sram_prefetch_counter == HBM_M_Prefetch_Amount) begin
                // Prefetching finished, reset the counter
                hbm_m_req_prefetch_data <= 1'b0;
                continuous_prefetch_m_en <= 1'b0;
                m_sram_prefetch_counter <= 'b0;
            end else begin
                hbm_m_req_prefetch_data <= 1'b0;
            end     
            m_sram_wen <= (hbm_m_req_prefetch_data && prefetch_m_valid);
        end
    end

    // -----------------------------
    // Vector SRAM
    // -----------------------------

    // Assuming the read cycle is 1 cycle for both ports.
    // Port A ->  R: Vector Operand (RS1)                           W: Vector Result from either Matrix or Vector Machine, 
    // Port B ->  R: Matrix Multiplicand Vector or HBM Write Data   W: Vector Prefetch

    logic [FIXED_DATA_WIDTH - 1 : 0] recorded_v_prefetch_addr;
    logic [FIXED_DATA_WIDTH - 1 : 0] recorded_v_load_addr_1, recorded_v_load_addr_2;
    logic [FIXED_DATA_WIDTH - 1 : 0] recorded_m_write_addr, recorded_v_write_addr;
    logic [FIXED_DATA_WIDTH - 1 : 0] hbm_waddr;
    logic continuous_v_prefetch_en, continuous_load_v_for_matrix_en;
    logic [M_LD_COUNT_WIDTH : 0] v_sram_load_for_matrix_counter;
    logic [V_PF_COUNT_WIDTH : 0] v_sram_prefetch_counter;
    logic v_v_a_load, v_v_b_load;

    always_comb begin
        // Port A Addr Mangement
        if (mem_stage_write_control.w_s_sram_port_a_en == 1'b1 && select_write_data_a == 1'b1) begin
            v_sram_addr_a = recorded_m_write_addr;
        end else if (mem_stage_write_control.w_s_sram_port_a_en == 1'b1 && select_write_data_a == 1'b0) begin
            v_sram_addr_a = recorded_v_write_addr;
        end else begin
            v_sram_addr_a = recorded_v_load_addr_1;
        end

        // Port B Addr Mangement
        if (continuous_v_prefetch_en) begin
            v_sram_addr_b = recorded_v_prefetch_addr;
        end else if (mem_stage_op.h_op == STORE_V) begin
            v_sram_addr_b = hbm_waddr;
        end else begin
            v_sram_addr_b = recorded_v_load_addr_2;
        end

        // Prefetch Record
        if (rst) begin
            recorded_v_prefetch_addr = 'b0;
            hbm_waddr = 'b0;
        end else if (exe_stage_op.h_op == PREFETCH_V) begin
            recorded_v_prefetch_addr = exe_stage_op.addr_2;
        end else if (exe_stage_op.h_op == STORE_V) begin
            hbm_waddr = exe_stage_op.addr_2;
        end
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            v_v_a_valid     <= 1'b0;
            v_v_b_valid     <= 1'b0;
            hbm_write_data_valid      <= 1'b0;
            recorded_v_load_addr_1  <= 'b0;
            recorded_v_load_addr_2  <= 'b0;
            recorded_m_write_addr   <= 'b0;
            recorded_v_write_addr   <= 'b0;
            m_v_valid       <= 1'b0;
            m_v_load        <= 1'b0;
            v_v_a_load      <= 1'b0;
            v_v_b_load      <= 1'b0;
            m_v_load_in_process <= 1'b0;
        end else begin
            v_v_a_valid                 <= v_v_a_load;
            v_v_b_valid                 <= v_v_b_load;
            hbm_write_data_valid        <= hbm_load_write_data;
            //Port A
            if(exe_stage_op.m_op != STALL_M && m_v_ready) begin
                // Read Vector from SRAM
                m_v_load        <= 1'b1;
                v_v_a_load      <= 1'b0;
                v_sram_req_a    <= 1'b1;
                v_sram_wen_a    <= 1'b0;
                continuous_load_v_for_matrix_en <= 1'b1;
                m_v_load_in_process <= 1'b1;
            end else if (continuous_load_v_for_matrix_en & m_v_ready) begin
                if (v_sram_load_for_matrix_counter == MATRIX_LOAD_ITERATION - 1) begin
                    m_sram_req <= 1'b0;
                    m_v_load   <= 1'b0;
                    v_sram_load_for_matrix_counter <= 'b0;
                    continuous_load_v_for_matrix_en <= 1'b0;
                    m_v_load_in_process <= 1'b0;
                end else begin
                    m_v_load    <= 1'b1;
                    m_sram_req  <= 1'b1;
                    v_sram_load_for_matrix_counter <= v_sram_load_for_matrix_counter + 1'b1;
                    m_v_load_in_process <= 1'b1;
                end
            end else if (exe_stage_op.v_ele_op != STALL_V_ELEMENT || exe_stage_op.v_reduct_op != STALL_V_REDUCT) begin
                m_v_load        <= 1'b0;
                v_v_a_load      <= 1'b1;
                v_sram_req_a    <= 1'b1;
                v_sram_wen_a    <= 1'b0;
            end else if (mem_write_control.w_s_sram_port_a_en == 1'b1) begin
                // Write the result from matrix machine to the s_sram
                m_v_load        <= 1'b0;
                v_v_a_load      <= 1'b0;
                v_sram_req_a    <= 1'b1;
                v_sram_wen_a    <= 1'b1;
            end else begin
                // No Scratchpad SRAM access request.
                m_v_load        <= 1'b0;
                v_v_a_load      <= 1'b0;
                v_sram_req_a    <= 1'b0;
                v_sram_wen_a    <= 1'b0;
            end

            // Write Data Selection
            if (m_out_valid && v_v_out_valid) begin
                // When the two data are ready at the same time, need to decide the priority. Now set the matrix machine to be higher priority.
                select_write_data_a <= 1'b1;
                v_v_out_ready       <= 1'b0;
            end else if (m_out_valid) begin    
                select_write_data_a <= 1'b1;
                v_v_out_ready       <= 1'b1;
            end else if (v_v_out_valid) begin
                select_write_data_a <= 1'b0;
                v_v_out_ready       <= 1'b1;
            end else begin
                select_write_data_a <= 1'b0;
                v_v_out_ready       <= 1'b1;
            end

            //Port B
            if (((exe_stage_op.v_ele_op != STALL_V_ELEMENT) && !exe_stage_op.v_broadcast_en) || (exe_stage_op.v_reduct_op != STALL_V_REDUCT)) begin
                // Read Port activated
                v_v_b_load          <= 1'b1;
                hbm_load_write_data <= 1'b0;
                v_sram_req_b        <= 1'b1;
                v_sram_wen_b        <= 1'b0;
            end else if (exe_stage_op.h_op == STORE_V & hbm_ready_to_write) begin
                v_v_b_load          <= 1'b0;
                hbm_load_write_data <= 1'b1;
                v_sram_req_b        <= 1'b1;
                v_sram_wen_b        <= 1'b0;
            end else if (mem_write_control.w_s_sram_port_b_en && prefetch_v_valid) begin
                // HBM Fetch to the scratchpad sram
                continuous_v_prefetch_en <= 1'b1;
                v_v_b_load          <= 1'b0;
                hbm_load_write_data <= 1'b0;
                v_sram_wen_b        <= 1'b1;
                v_sram_req_b        <= 1'b1;
            end else if (continuous_v_prefetch_en & v_sram_prefetch_counter < HBM_V_Prefetch_Amount & prefetch_m_valid) begin
                v_sram_wen_b        <= 1'b1;
                v_sram_req_b        <= 1'b1;
                v_sram_prefetch_counter <= v_sram_prefetch_counter + 'b1;
            end else if (v_sram_prefetch_counter == HBM_V_Prefetch_Amount) begin
                // Prefetching finished, reset the counter
                v_sram_wen_b        <= 1'b0;
                v_sram_req_b        <= 1'b0;
                continuous_v_prefetch_en <= 1'b0;
                v_sram_prefetch_counter <= 'b0;
            end else begin
                // No SRAM access
                v_sram_req_b        <= 1'b0;
                v_sram_wen_b        <= 1'b0;
                hbm_load_write_data   <= 1'b0;
                v_v_b_load          <= 1'b0;
            end
            
            recorded_v_load_addr_1 <= exe_stage_op.addr_1;
            recorded_v_load_addr_2 <= exe_stage_op.addr_2;

            if (m_write_request) begin
                recorded_m_write_addr <= m_write_addr;
            end else begin
                recorded_m_write_addr <= recorded_m_write_addr;
            end

            if (v_write_request) begin
                recorded_v_write_addr <= v_write_addr;
            end else begin
                recorded_v_write_addr <= recorded_v_write_addr;
            end

            m_v_valid <= m_v_load;
        end

    end

    // Scalar Data Forwarding to Vector Machine
    always_ff @(posedge clk) begin
        if (rst) begin
            v_s_in_valid <= 1'b0;
        end else begin
            if ((((exe_stage_op.v_broadcast_en == 1'b1)  & (exe_stage_op.v_ele_op != STALL_V_ELEMENT)) || (exe_stage_op.v_reduct_op != STALL_V_REDUCT)) & v_s_in_ready) begin
                v_s_in_valid <= 1'b1;
            end else begin
                v_s_in_valid <= 1'b0;
            end
        end
    end

endmodule

