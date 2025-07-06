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

module data_flow_control import precision_pkg::*; import configuration_pkg::*; #(
    localparam MATRIX_LOAD_ITERATION_GEMM   = BLEN,
    localparam MATRIX_LOAD_ITERATION_GEMV   = MLEN,
    localparam BLOCK_NUM                    = VLEN / BLOCK_DIM
) (

    input       logic clk,
    input       logic rst,

    // Current Execution
    input       OP_BUNDLE                       exe_stage_op,
    input       MEM_WEN_INFO                    mem_write_control,
    output      MEM_WREQ_INFO                   write_req,

    // Interface with Matrix Machine
    input       logic m_m_ready,
    output      logic m_m_valid,
    output      logic m_v_valid,
    input       logic m_v_ready,
    input       logic m_out_valid,
    output      logic m_out_ready,
    // output      logic m_complete_acc_writeback,
    input       logic [1:0] m_write_request,
    input       logic [FIXED_DATA_WIDTH - 1 : 0] m_write_addr,

    // Interface with Matrix SRAM
    output      logic [FIXED_DATA_WIDTH - 1 : 0] m_sram_raddr,
    output      logic [FIXED_DATA_WIDTH - 1 : 0] m_sram_waddr,
    output      logic m_sram_wen,
    output      logic m_sram_req,
    output      logic m_sram_transposed_read,
    input       logic m_prefetch_data_not_ready,

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
    input       logic [FIXED_DATA_WIDTH - 1 : 0]    v_write_addr,

    // Interface with Vector SRAM
    output      logic v_sram_req_a,
    output      logic v_sram_wen_a,
    output      logic [FIXED_DATA_WIDTH - 1 : 0]    v_sram_addr_a,
    output      logic [VLEN-1:0]                    v_sram_mask_a,
    output      logic select_write_data_a,          

    output      logic v_sram_req_b,
    output      logic [1:0] v_sram_mxfp_req_b,
    output      logic v_sram_wen_b,
    output      logic [FIXED_DATA_WIDTH - 1 : 0]    v_sram_addr_b,
    output      logic [VLEN-1:0]                    v_sram_mask_b,

    input       logic v_prefetch_data_not_ready,

    // Interface with HBM
    input       logic prefetch_m_valid,
    input       logic prefetch_v_valid,
    input       logic hbm_ready_to_write,
    output      logic hbm_m_req_prefetch_data,
    output      logic hbm_v_req_prefetch_data
);
    // Package Imports
    import pipeline_pkg::MAX_PIPELINE_STAGE;
    import configuration_pkg::*;

    localparam M_LD_COUNT_WIDTH = $clog2(MATRIX_LOAD_ITERATION_GEMV);
    localparam M_PF_COUNT_WIDTH = $clog2(HBM_M_Prefetch_Amount);
    localparam V_PF_COUNT_WIDTH = $clog2(HBM_V_Prefetch_Amount);
    localparam HBM_WRITE_AMOUNT = HBM_V_Writeback_Amount + 2;   // 2 for 
    localparam H_WR_COUNT_WIDTH = $clog2(HBM_WRITE_AMOUNT);


    // Memory Execution Control and Dependency Monitor
    localparam MSRAM_BYTES_PER_ROW =  (LOW_MXFP_EXP_WIDTH + LOW_MXFP_MANT_WIDTH + 1) * MLEN * Matrix_Parallel_Rd_Dim / 8;
    localparam VSRAM_BYTES_PER_ROW =  (HIGH_MXFP_EXP_WIDTH + HIGH_MXFP_MANT_WIDTH + 1) * VLEN / 8;
    OP_BUNDLE  mem_stage_op;
    MEM_WEN_INFO mem_stage_write_control;

    always_ff @(posedge clk ) begin
        mem_stage_op            <= exe_stage_op;
        mem_stage_write_control <= mem_write_control;
    end

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
        write_req.wreq_m_sram        = ((prefetch_m_valid == 1'b1) & (previous_dma_m_ready == 1'b0))    ? 1'b1 : 1'b0;
        write_req.wreq_s_sram_port_a = ((m_write_request  == 1'b1)  | (v_write_request == 1'b1))         ? 1'b1 : 1'b0;
        write_req.wreq_s_sram_port_b = ((prefetch_v_valid == 1'b1) & (previous_dma_v_ready == 1'b0))    ? 1'b1 : 1'b0;
        write_req.wreq_from_m        = m_write_request;
    end

    
    // -----------------------------
    // Matrix SRAM
    // -----------------------------
    logic [FIXED_DATA_WIDTH - 1 : 0] recorded_m_prefetch_addr, recorded_m_load_addr;
    logic [FIXED_DATA_WIDTH - 1 : 0] m_sram_raddr_offset;
    logic continuous_load_m_en, continuous_prefetch_m_en;
    logic [M_LD_COUNT_WIDTH : 0] m_sram_load_counter, load_m_amount;
    logic [M_LD_COUNT_WIDTH : 0] recorded_m_sram_load_counter;
    logic [M_PF_COUNT_WIDTH : 0] m_sram_prefetch_counter;
    logic m_m_load, m_v_load;
    logic p2_m_m_load, p1_m_m_load, m_v_load_cond;
    logic matrix_related_data_ready;
    assign matrix_related_data_ready = (!m_prefetch_data_not_ready) & (!v_prefetch_data_not_ready);


    // Update addr only when the exe operation is MV_IC or MV_WO
    always_comb begin
        if (continuous_load_m_en) begin
            if (matrix_related_data_ready) begin
                m_sram_raddr_offset = m_sram_load_counter * MSRAM_BYTES_PER_ROW;
            end else if (((continuous_load_m_en & (!m_m_ready)) || !matrix_related_data_ready)) begin
                m_sram_raddr_offset = recorded_m_sram_load_counter * MSRAM_BYTES_PER_ROW;
            end
        end else begin
            m_sram_raddr_offset = 'b0;
        end

        if ((mem_stage_op.m_op != STALL_M & mem_stage_op.m_op != MM_WO)|| continuous_load_m_en) begin
            m_sram_raddr = recorded_m_load_addr + m_sram_raddr_offset;
        end else begin
            m_sram_raddr = 'b0;
        end

        if (continuous_prefetch_m_en) begin
            m_sram_waddr = recorded_m_prefetch_addr + m_sram_prefetch_counter * MSRAM_BYTES_PER_ROW;
        end else begin
            m_sram_waddr = 'b0;
        end
    end

    // Read  Port -> Matrix Weight Load
    // Write Port -> Matrix Weight Prefetch

    logic end_of_load_m; // TODO: Maybe this can be optimised.
    logic p1_matrix_related_data_ready;

    always_ff @(posedge clk) begin
        if (rst) begin
            m_sram_req <= 1'b0;
            hbm_m_req_prefetch_data     <= 1'b0;
            continuous_load_m_en        <= 1'b0;
            continuous_prefetch_m_en    <= 1'b0;
            p1_matrix_related_data_ready <= 1'b0;
            m_sram_load_counter         <= 'b0;
            load_m_amount               <= 'b0;
            m_sram_prefetch_counter     <= 'b0;
            m_m_load                    <= 1'b0;
            p1_m_m_load                 <= 1'b0;
            p2_m_m_load                 <= 1'b0;
            m_m_valid                   <= 1'b0;
            m_out_ready                 <= 1'b0;
            recorded_m_prefetch_addr    <= 'b0;
            recorded_m_load_addr        <= 'b0;
            recorded_m_sram_load_counter <= 'b0;
            end_of_load_m              <= 1'b0;
        end else begin
            // Address Management
            if (exe_stage_op.h_op == PREFETCH_M_C) begin
                recorded_m_prefetch_addr <= exe_stage_op.addr_2;
            end else if (exe_stage_op.m_op != STALL_M & exe_stage_op.m_op != MM_WO & exe_stage_op.m_op != MV_WO) begin
                recorded_m_load_addr <= exe_stage_op.addr_2;
            end 
            if (matrix_related_data_ready) begin
                recorded_m_sram_load_counter <= m_sram_load_counter;
            end 

            m_out_ready     <= 1'b1;
            p1_m_m_load     <= m_m_load & !end_of_load_m;
            p2_m_m_load     <= p1_m_m_load;
            p1_matrix_related_data_ready <= matrix_related_data_ready;
        
            // Matrix SRAM Read Port Control
            if (exe_stage_op.m_op != STALL_M & exe_stage_op.m_op != MM_WO & exe_stage_op.m_op != MV_WO) begin
                m_sram_req      <= 1'b1;
                m_m_load        <= 1'b1;
                m_sram_transposed_read  <= exe_stage_op.m_transposed_read;
                m_sram_load_counter     <= 'b0;
                load_m_amount           <= (exe_stage_op.m_op == MV_IC) ? MATRIX_LOAD_ITERATION_GEMV: MATRIX_LOAD_ITERATION_GEMM;
                continuous_load_m_en    <= 1'b1;
            end else if (continuous_load_m_en) begin
                end_of_load_m   <= (m_sram_load_counter == load_m_amount) & m_m_ready;
                if (m_m_ready) begin
                    m_m_valid <= (p2_m_m_load & p1_m_m_load & !end_of_load_m) & (p1_matrix_related_data_ready) & (matrix_related_data_ready); // 2 cycles for loading the matrix data
                    if (end_of_load_m) begin
                        m_sram_req <= 1'b0;
                        m_m_load   <= 1'b0;
                        m_sram_load_counter <= 'b0;
                        continuous_load_m_en <= 1'b0;
                    end else begin
                        if (p1_m_m_load & matrix_related_data_ready) begin
                            m_m_load    <= 1'b1;
                            m_sram_req  <= 1'b1;
                            m_sram_load_counter <= m_sram_load_counter + 1'b1;
                        end else begin
                            m_m_load    <= 1'b1;
                            m_sram_req  <= 1'b1;
                            continuous_load_m_en <= 1'b1;
                        end
                    end   
                end

            end else begin
                m_m_load   <= 1'b0;
                m_sram_req <= 1'b0;
                continuous_load_m_en <= 1'b0;
            end

            // Matrix SRAM Write Port Control
            if (mem_write_control.w_m_sram_en == 1'b1 && prefetch_m_valid) begin
                //At the start
                hbm_m_req_prefetch_data     <= 1'b1;
                continuous_prefetch_m_en    <= 1'b1;
                m_sram_prefetch_counter     <= 'b0;
            end else if (continuous_prefetch_m_en & m_sram_prefetch_counter < HBM_M_Prefetch_Amount & m_sram_wen) begin
                hbm_m_req_prefetch_data <= 1'b1;
                m_sram_prefetch_counter <= m_sram_prefetch_counter + 'b1;

            end else if (m_sram_prefetch_counter == HBM_M_Prefetch_Amount) begin
                // Prefetching finished, reset the counter
                hbm_m_req_prefetch_data <= 1'b0;
                continuous_prefetch_m_en <= 1'b0;
                m_sram_prefetch_counter <= 'b0;
            end 
            m_sram_wen <= (hbm_m_req_prefetch_data && prefetch_m_valid);
        end
    end

    // -----------------------------
    // Vector SRAM
    // -----------------------------

    // Assuming the read cycle is 1 cycle for both ports.
    // Port A ->  R: Matrix Multiplicand Vector & Vector Operand (RS1)                          W: Vector Result from either Matrix or Vector Machine, 
    // Port B ->  R: Vector Operand (RS2)  or Load HBM Write Data                               W: Vector Prefetch
    // For Port A, if loading it to the matrix machine, this takes extra cycle as we need to quantise the fp data (activation) into MX-FP format.

    logic [FIXED_DATA_WIDTH - 1 : 0] recorded_v_prefetch_addr;
    logic [FIXED_DATA_WIDTH - 1 : 0] recorded_v_load_for_matrix_addr;
    logic [FIXED_DATA_WIDTH - 1 : 0] recorded_v_load_addr_1, recorded_v_load_addr_2;
    logic [FIXED_DATA_WIDTH - 1 : 0] recorded_m_write_addr, recorded_v_write_addr;
    logic [FIXED_DATA_WIDTH - 1 : 0] hbm_waddr;
    logic port_b_prefetch_ready;
    logic continuous_v_prefetch_en, continuous_load_v_for_matrix_en, continuous_v_write_from_matrix_en, continuous_write_to_hbm;
    logic [M_LD_COUNT_WIDTH : 0] v_sram_load_for_matrix_counter, v_sram_write_from_matrix_counter;
    logic load_for_gemv_en;
    logic [V_PF_COUNT_WIDTH : 0] v_sram_prefetch_counter;
    logic [H_WR_COUNT_WIDTH : 0] hbm_write_counter;
    logic v_v_a_load, v_v_b_load;
    logic end_of_load_v_for_matrix;
    logic p1_vport_a_load_valid, p2_vport_a_load_valid;
    
    always_comb begin
        // Port A Addr Mangement
         if (continuous_load_v_for_matrix_en) begin
            select_write_data_a = 1'b0;
            v_sram_addr_a = recorded_v_load_for_matrix_addr + v_sram_load_for_matrix_counter * VSRAM_BYTES_PER_ROW;
        end else if (continuous_v_write_from_matrix_en) begin
            select_write_data_a = 1'b1;
            v_sram_mask_a = {MLEN{1'b1}};
            v_sram_addr_a = recorded_m_write_addr + v_sram_write_from_matrix_counter * VSRAM_BYTES_PER_ROW;
        end else if (mem_stage_write_control.w_s_sram_port_a_en == 1'b1 && select_write_data_a == 1'b0) begin
            select_write_data_a = 1'b0;
            v_sram_mask_a = {VLEN{1'b1}};
            v_sram_addr_a = recorded_v_write_addr;
        end else begin
            select_write_data_a = 1'b0;
            v_sram_addr_a = recorded_v_load_addr_1;
        end

        // Port B Addr Mangement
        v_sram_mask_b = {VLEN{1'b1}};
        if (continuous_v_prefetch_en) begin
            v_sram_addr_b = recorded_v_prefetch_addr + v_sram_prefetch_counter * VSRAM_BYTES_PER_ROW;
        end else if (continuous_write_to_hbm) begin
            v_sram_addr_b = hbm_waddr + hbm_write_counter * VSRAM_BYTES_PER_ROW;
        end else begin
            v_sram_addr_b = recorded_v_load_addr_2;
        end

        // Prefetch Record
        if (rst) begin
            recorded_v_prefetch_addr = 'b0;
            hbm_waddr = 'b0;
        end else if (exe_stage_op.h_op == PREFETCH_V_C) begin
            recorded_v_prefetch_addr = exe_stage_op.addr_2;
        end else if (exe_stage_op.h_op == STORE_V_S || exe_stage_op.h_op == STORE_V_C) begin
            hbm_waddr = exe_stage_op.addr_2;
        end
    end

    assign end_of_load_v_for_matrix = (v_sram_load_for_matrix_counter == MATRIX_LOAD_ITERATION_GEMM ) & (matrix_related_data_ready) & m_v_ready;

    always_ff @(posedge clk) begin
        if (rst) begin
            v_v_a_valid     <= 1'b0;
            v_v_b_valid     <= 1'b0;
            hbm_v_req_prefetch_data         <= 1'b0;
            recorded_v_load_addr_1          <= 'b0;
            recorded_v_load_addr_2          <= 'b0;
            recorded_v_load_for_matrix_addr <= 'b0;
            recorded_m_write_addr           <= 'b0;
            recorded_v_write_addr           <= 'b0;
            load_for_gemv_en                <= 1'b0;
            p1_vport_a_load_valid           <= 1'b0;
            p2_vport_a_load_valid           <= 1'b0;
            m_v_valid                       <= 1'b0;
            m_v_load                        <= 1'b0;
            v_v_a_load                      <= 1'b0;
            v_v_b_load                      <= 1'b0;
            m_v_load_cond                   <= 1'b0;
            port_b_prefetch_ready           <= 1'b0;
            continuous_v_write_from_matrix_en   <= 1'b0;
            continuous_load_v_for_matrix_en     <= 1'b0;
            v_v_out_ready                   <= 1'b0;
            // m_complete_acc_writeback        <= 1'b0;
            v_sram_mxfp_req_b               <= 2'b0;
            v_sram_req_b                    <= 1'b0;
            v_sram_req_a                    <= 1'b0;
            hbm_write_counter               <= 'b0;
            v_sram_load_for_matrix_counter  <= 'b0;
            v_sram_write_from_matrix_counter <= 'b0;

        end else begin
            v_v_out_ready               <= 1'b1;
            v_v_a_valid                 <= v_v_a_load;
            v_v_b_valid                 <= v_v_b_load;
            m_v_load_cond               <= m_v_load & !end_of_load_v_for_matrix;
            m_v_valid                   <= (m_v_load_cond & !end_of_load_v_for_matrix ) & (matrix_related_data_ready);
            //Port A
            if((exe_stage_op.m_op != STALL_M & exe_stage_op.m_op != MM_WO & exe_stage_op.m_op != MV_WO) & m_v_ready) begin
                // Read Vector from SRAM
                m_v_load        <= 1'b1;
                v_v_a_load      <= 1'b0;
                v_sram_req_a    <= 1'b1;
                v_sram_wen_a    <= 1'b0;
                continuous_load_v_for_matrix_en <= 1'b1;
                load_for_gemv_en <= (exe_stage_op.m_op == MV_IC) ? 1'b1 : 1'b0;
            
            end else if (continuous_load_v_for_matrix_en) begin
                if (m_v_ready) begin
                    if (!load_for_gemv_en & end_of_load_v_for_matrix) begin
                        v_sram_req_a <= 1'b0;
                        m_v_load   <= 1'b0;
                        v_sram_load_for_matrix_counter <= 'b0;
                        continuous_load_v_for_matrix_en <= 1'b0;
                    end else begin
                        if (matrix_related_data_ready & m_v_load_cond) begin
                            if (load_for_gemv_en) begin
                                m_v_load                        <= 1'b0;
                                v_sram_req_a                    <= 1'b0;
                                v_sram_load_for_matrix_counter  <= 'b0;
                                continuous_load_v_for_matrix_en <= 1'b0;
                                load_for_gemv_en                <= 1'b0;
                            end else begin
                                m_v_load                        <= 1'b1;
                                v_sram_req_a                    <= 1'b1;
                                v_sram_load_for_matrix_counter  <= v_sram_load_for_matrix_counter + 1'b1;
                            end
                        end else begin
                            m_v_load    <= 1'b1;
                            v_sram_req_a <= 1'b1;
                            continuous_load_v_for_matrix_en <= 1'b1;
                        end
                    end 
                end
            end else if (exe_stage_op.v_ele_op != STALL_V_ELEMENT || exe_stage_op.v_reduct_op != STALL_V_REDUCT) begin
                // TODO: Need to introduce v_prefetch_data_not_ready for vector machine
                m_v_load        <= 1'b0;
                v_v_a_load      <= 1'b1;
                v_sram_req_a    <= 1'b1;
                v_sram_wen_a    <= 1'b0;
            end else if (continuous_v_write_from_matrix_en & m_out_valid) begin
                if (v_sram_write_from_matrix_counter < MATRIX_LOAD_ITERATION_GEMM - 1) begin
                    m_v_load        <= 1'b0;
                    v_v_a_load      <= 1'b0;
                    v_sram_req_a    <= 1'b1;
                    v_sram_wen_a    <= 1'b1;           
                    v_sram_write_from_matrix_counter <= v_sram_write_from_matrix_counter + 1'b1;
                end else begin
                    m_v_load        <= 1'b0;
                    v_v_a_load      <= 1'b0;
                    v_sram_req_a    <= 1'b0;
                    v_sram_wen_a    <= 1'b0;           
                    continuous_v_write_from_matrix_en <= 1'b0;         
                end
            end else if (mem_write_control.w_s_sram_port_a_en == 1'b1) begin
                if (mem_write_control.w_from_m) begin
                    // Write the result from matrix machine to the s_sram
                    m_v_load        <= 1'b0;
                    v_v_a_load      <= 1'b0;
                    v_sram_req_a    <= 1'b1;
                    v_sram_wen_a    <= 1'b1;           
                    continuous_v_write_from_matrix_en <= 1'b1;         
                    v_sram_write_from_matrix_counter <= 'b0;
                end else begin
                    // Write the result from vector machine to the s_sram
                    m_v_load        <= 1'b0;
                    v_v_a_load      <= 1'b0;
                    v_sram_req_a    <= 1'b1;
                    v_sram_wen_a    <= 1'b1;                    
                end
            end else begin
                // No Scratchpad SRAM access request.
                m_v_load        <= 1'b0;
                v_v_a_load      <= 1'b0;
                v_sram_req_a    <= 1'b0;
                v_sram_wen_a    <= 1'b0;
            end

            //Port B
            if (((exe_stage_op.v_ele_op != STALL_V_ELEMENT) && !exe_stage_op.v_broadcast_en) || (exe_stage_op.v_reduct_op != STALL_V_REDUCT)) begin
                // Read Port activated
                v_v_b_load                  <= 1'b1;
            end else if ((exe_stage_op.h_op == STORE_V_C || exe_stage_op.h_op == STORE_V_S) & hbm_ready_to_write) begin
                // Start HBM Writeback to the scratchpad sram
                continuous_write_to_hbm     <= 1'b1;
                hbm_write_counter           <= 'b0;
                v_v_b_load                  <= 1'b0;
                v_sram_mxfp_req_b           <= (exe_stage_op.h_op == STORE_V_C) ? 2'b01 : 2'b10; // 01 for C, 10 for S
            end else if (continuous_write_to_hbm && hbm_write_counter < HBM_WRITE_AMOUNT && hbm_ready_to_write) begin
                // Intermediate HBM Writeback to the scratchpad sram
                v_sram_mxfp_req_b           <= v_sram_mxfp_req_b;
                v_v_b_load                  <= 1'b1;
                hbm_write_counter           <= hbm_write_counter + 'b1;
            end else if (hbm_write_counter == HBM_WRITE_AMOUNT && hbm_ready_to_write) begin
                // Finish HBM Writeback, reset the counter
                v_sram_mxfp_req_b           <= 2'b0;
                v_v_b_load                  <= 1'b0;
                continuous_write_to_hbm     <= 1'b0;
                hbm_write_counter           <= 'b0;
            end else if (mem_write_control.w_s_sram_port_b_en && prefetch_v_valid) begin
                // Start HBM Fetch to the scratchpad sram
                continuous_v_prefetch_en        <= 1'b1;
                v_v_b_load                      <= 1'b0;
                hbm_v_req_prefetch_data         <= 1'b1;
            end else if (continuous_v_prefetch_en & v_sram_prefetch_counter < HBM_V_Prefetch_Amount & v_sram_wen_b) begin
                 // Intermediate HBM Fetch to the scratchpad sram
                hbm_v_req_prefetch_data         <= 1'b1;
                v_sram_prefetch_counter         <= v_sram_prefetch_counter + 'b1;
            end else if (v_sram_prefetch_counter == HBM_V_Prefetch_Amount) begin
                // Finish Prefetching, reset the counter
                hbm_v_req_prefetch_data         <= 1'b0;
                continuous_v_prefetch_en        <= 1'b0;
                v_sram_prefetch_counter         <= 'b0;
            end  else begin
                
            end

            if (hbm_v_req_prefetch_data && prefetch_v_valid) begin
                v_sram_req_b            <= 1'b1;
            end else if (((exe_stage_op.v_ele_op != STALL_V_ELEMENT) && !exe_stage_op.v_broadcast_en) || (exe_stage_op.v_reduct_op != STALL_V_REDUCT)) begin
                v_sram_req_b            <= 1'b1;
            end else begin
                v_sram_req_b            <= 1'b0;
            end

            v_sram_wen_b            <= (hbm_v_req_prefetch_data && prefetch_v_valid);
            
            recorded_v_load_addr_1  <= exe_stage_op.addr_1;
            recorded_v_load_addr_2  <= exe_stage_op.addr_2;
            
            if (exe_stage_op.m_op != STALL_M & exe_stage_op.m_op != MM_WO & exe_stage_op.m_op != MV_WO) begin
                recorded_v_load_for_matrix_addr <= exe_stage_op.addr_1;
            end

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

