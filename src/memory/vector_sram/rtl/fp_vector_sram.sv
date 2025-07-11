`timescale 1ns/1ps

/*
Module      : Top Level SRAM design for scratchpad
Timing      : Sequential Logic, 3 cycle for MXFP read and 1 cycle for FP read
Description :
            : This module supports two port reading
            : The addressing mode is Little Endian.
            : Port A ->  R: Matrix Multiplicand Vector or Vector Operand (RS1)               W: Vector Result from either Matrix or Vector Machine, 
            : Port B ->  R: Matrix Offest Vector or Vector Operand (RS2) or HBM Write Data   W: Vector Prefetch
Status      :
*/

module fp_vector_sram #(
    
    // MX-FP Data Format
    parameter   HIGH_MXFP_EXP_WIDTH     = 4,
    parameter   HIGH_MXFP_MANT_WIDTH    = 3,
    parameter   LOW_MXFP_EXP_WIDTH      = 4,
    parameter   LOW_MXFP_MANT_WIDTH     = 3,
    parameter   MXFP_SCALE_WIDTH        = 8,
    // FP Data Format
    parameter   EXP_WIDTH               = 8,                                  
    parameter   MANT_WIDTH              = 7,

    // Dimension
    parameter   VLEN                    = 8,   
    parameter   MLEN                    = 8, 
    parameter   BLOCK_DIM               = 4,
    localparam  M_BLOCK_NUM             = MLEN / BLOCK_DIM,                                
    localparam  V_BLOCK_NUM             = VLEN / BLOCK_DIM,

    // SRAM
    parameter   SRAM_DEPTH              = 128,
    parameter   ON_CHIP_ADDR_WIDTH      = 32,
    parameter   PREFETCH_AMOUNT         = 4,
    parameter   VECTOR_RESET_AMOUNT     = 8
    // For Debugging
    `ifdef SIMULATION
        ,parameter string MEM_RESULT_FILE = ""
    `endif

)(
    input   logic clk,
    input   logic rst,

    // Port A
    input   logic port_a_req,
    input   logic port_a_write_en,
    input   logic [ON_CHIP_ADDR_WIDTH - 1 : 0] port_a_addr,
    input   logic select_write_data_a, // 0 for Vector Machine, 1 for Matrix Machine, 2 for Scalar Machine
    input   logic region_reset_a,
    input   logic [ON_CHIP_ADDR_WIDTH - 1 : 0] reset_addr_a,
    // FP Data Connection
    input   logic [VLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0]                port_a_v_fp_in,
    input   logic [MLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0]                port_a_m_fp_in,
    input   logic [VLEN - 1 : 0]                                                    port_a_mask_in,
    output  logic [VLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0]                port_a_v_fp_out,

    output  logic [MLEN - 1 : 0]            [HIGH_MXFP_EXP_WIDTH + HIGH_MXFP_MANT_WIDTH : 0]    port_a_element_out,
    output  logic [M_BLOCK_NUM - 1 : 0]     [MXFP_SCALE_WIDTH - 1 : 0]                          port_a_scale_out,

    // Port B
    input   logic port_b_req,
    input   logic port_b_write_en,
    input   logic [ON_CHIP_ADDR_WIDTH - 1 : 0] port_b_addr,
    input   logic select_write_data_b,
    // FP Data Connection
    input   logic [MLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0]                port_b_fp_in,
    output  logic [VLEN - 1 : 0]         [EXP_WIDTH + MANT_WIDTH : 0]               port_b_fp_out,
    input   logic [VLEN - 1 : 0]                                                    port_b_mask_in,
    // MX-FP Connection
    input   logic [VLEN - 1 : 0]            [HIGH_MXFP_EXP_WIDTH + HIGH_MXFP_MANT_WIDTH : 0]    port_b_element_in,
    input   logic [V_BLOCK_NUM - 1 : 0]     [MXFP_SCALE_WIDTH - 1 : 0]                          port_b_scale_in,

    input   logic [1:0] port_b_mxfp_req , // 0 for STALL, 1 for High Precision MXFP Load, 2 for Low Precision MXFP Load
    output  logic port_b_mxfp_high_out_valid,
    output  logic [VLEN - 1 : 0]            [HIGH_MXFP_EXP_WIDTH + HIGH_MXFP_MANT_WIDTH : 0]    port_b_high_element_out,
    output  logic [V_BLOCK_NUM - 1 : 0]     [MXFP_SCALE_WIDTH - 1 : 0]                          port_b_high_scale_out,
    
    output  logic port_b_mxfp_low_out_valid,
    output  logic [VLEN - 1 : 0]            [LOW_MXFP_EXP_WIDTH + LOW_MXFP_MANT_WIDTH : 0]      port_b_low_element_out,
    output  logic [V_BLOCK_NUM - 1 : 0]     [MXFP_SCALE_WIDTH - 1 : 0]                          port_b_low_scale_out,

    // Status Tracking for Prefetch
    input   logic prefetch_en,
    input   logic [ON_CHIP_ADDR_WIDTH - 1 : 0] prefetch_addr,
    output  logic reset_in_progress,
    output  logic data_not_ready
);

    localparam  INTERNAL_ADDR_LEN           = $clog2(SRAM_DEPTH);

    initial begin
        if (VLEN < MLEN) begin
            $error("VLEN must be greater than or equal to MLEN, but got VLEN = %0d, MLEN = %0d", VLEN, MLEN);
            $finish;
        end
    end

    logic [VLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0] port_a_fp_out_internal;
    logic [VLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0] port_a_fp_in_internal;
    logic [VLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0] port_b_fp_in_internal;
    logic [VLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0] port_b_fp_out_internal;
    logic [VLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0] converted_b_fp_in;
    logic [INTERNAL_ADDR_LEN - 1 : 0] reset_counter;
    logic port_a_write_en_internal;
    
    // -----------------------------
    // Prefetch Tag Tracking
    // -----------------------------

    // Tag Matching, trackinng the prefetch status.
    logic [INTERNAL_ADDR_LEN - 1 : 0]     translated_port_b_addr, translated_port_a_addr, translated_port_a_reset_addr, translated_prefetch_addr, translated_port_a_addr_internal;
    logic [INTERNAL_ADDR_LEN - 1 : 0]     recorded_translated_port_a_reset_addr;
    logic [SRAM_DEPTH - 1 : 0]            mem_data_tag;
    
    localparam BITWIDTH_PER_ROW         = (HIGH_MXFP_EXP_WIDTH + HIGH_MXFP_MANT_WIDTH + 1) * VLEN / 8;
    assign translated_port_a_addr       = port_a_addr >> $clog2(BITWIDTH_PER_ROW);
    assign translated_port_b_addr       = port_b_addr >> $clog2(BITWIDTH_PER_ROW);
    assign translated_port_a_reset_addr = reset_addr_a >> $clog2(BITWIDTH_PER_ROW);
    assign translated_prefetch_addr     = prefetch_addr >> $clog2(BITWIDTH_PER_ROW);

    always_ff @(posedge clk) begin
        if (rst) begin
            mem_data_tag <= {{SRAM_DEPTH{1'b1}}};
        end else if (prefetch_en) begin
            for (int i = 0; i < PREFETCH_AMOUNT; i++) begin
                mem_data_tag[translated_prefetch_addr + i] <= 1'b0;
            end
        end else if (port_b_write_en) begin
            mem_data_tag[translated_port_b_addr] <= 1'b1;
        end
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            data_not_ready <= 1'b0;
        end else begin
            data_not_ready <=  (port_b_req & !(&mem_data_tag[translated_port_b_addr +: VLEN])) || 
                               (port_a_req & !(&mem_data_tag[translated_port_a_addr +: VLEN]));
        end
    end

    // -----------------------------
    // Port A Management
    // -----------------------------

    always_comb begin
        if (select_write_data_a == 1'b0) begin
            // Vector Machine Mode, output as FP Data
            port_a_fp_in_internal       = port_a_v_fp_in;
            port_a_v_fp_out             = port_a_fp_out_internal;
            port_a_write_en_internal    = port_a_write_en;
            translated_port_a_addr_internal        = translated_port_a_addr;
        end else if (reset_in_progress) begin
            // Vector Machine Mode, output as FP Data
            port_a_fp_in_internal       = '0;
            port_a_v_fp_out             = '0;
            port_a_write_en_internal    = 1'b1;
            translated_port_a_addr_internal        = recorded_translated_port_a_reset_addr + reset_counter;
        end else begin
            // Matrix Machine Mode, output as MX-FP Data
            port_a_fp_in_internal       = port_a_m_fp_in;
            port_a_v_fp_out             = '0;
            port_a_write_en_internal    = port_a_write_en;
            translated_port_a_addr_internal        = translated_port_a_addr;
        end 
    end

    // Convert FP Data to MX-FP Data for HBM write
    logic [V_BLOCK_NUM - 1 : 0] mxfp_fp_convert_port_a_in_valid;
    logic [V_BLOCK_NUM - 1 : 0] mxfp_fp_convert_port_a_out_ready;
    logic [V_BLOCK_NUM - 1 : 0] mxfp_fp_convert_port_a_out_valid;
    logic port_a_mxfp_out_valid;
    logic mxfp_fp_convert_port_a_ready;
    
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            mxfp_fp_convert_port_a_in_valid <= '0;
            mxfp_fp_convert_port_a_ready    <= 1'b0;
            reset_in_progress               <= 1'b0;    
            reset_counter                   <= '0;
            recorded_translated_port_a_reset_addr <= '0;
        end else begin
            mxfp_fp_convert_port_a_in_valid <= (select_write_data_a == 1'b0 && port_a_req) ? {V_BLOCK_NUM{1'b1}} : '0;
            mxfp_fp_convert_port_a_ready <= 1'b1;
            if (region_reset_a) begin
                reset_in_progress   <= 1'b1;
                reset_counter       <= '0;
                recorded_translated_port_a_reset_addr <= translated_port_a_reset_addr;
            end else if (reset_counter == VECTOR_RESET_AMOUNT - 1) begin
                reset_in_progress   <= 1'b0;
                reset_counter       <= '0;
                recorded_translated_port_a_reset_addr <= '0;
            end else if (reset_in_progress) begin
                reset_counter <= reset_counter + 'b1;
            end else begin
                reset_counter <= '0;
            end
        end
    end

    for (genvar j = 0; j < M_BLOCK_NUM; j++) begin
        fp_2_mx_fp_block #(
            .BLOCK_DIM          (BLOCK_DIM),
            .FP_MANT_WIDTH      (MANT_WIDTH),
            .FP_EXP_WIDTH       (EXP_WIDTH),
            .MXFP_MANT_WIDTH    (HIGH_MXFP_MANT_WIDTH),
            .MXFP_EXP_WIDTH     (HIGH_MXFP_EXP_WIDTH),
            .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH)
        ) fp_2_mx_port_a_convert_init(
            .clk(clk),
            .rst(rst),
            .data_in                (port_a_fp_out_internal[j * BLOCK_DIM +: BLOCK_DIM]),
            .data_in_valid          (mxfp_fp_convert_port_a_in_valid[j]),
            .data_in_ready          (),
            .element_data_out       (port_a_element_out[j * BLOCK_DIM +: BLOCK_DIM]),
            .scale_data_out         (port_a_scale_out[j]),
            .mx_fp_data_out_valid   (mxfp_fp_convert_port_a_out_valid[j]),
            .mx_fp_data_out_ready   (mxfp_fp_convert_port_a_out_ready[j])
        );
    end

    join_n #(
        .NUM_HANDSHAKES(V_BLOCK_NUM)
    ) mxfp_fp_convert_port_a_join (
        .data_in_valid(mxfp_fp_convert_port_a_out_valid),
        .data_in_ready(mxfp_fp_convert_port_a_out_ready),
        .data_out_valid(port_a_mxfp_out_valid),
        .data_out_ready(mxfp_fp_convert_port_a_ready)
    );


    // -----------------------------
    // Port B Management
    // -----------------------------
    logic   mxfp_fp_convert_port_b_ready;
    assign  port_b_fp_out = port_b_fp_out_internal;

    always_comb begin
        if (select_write_data_b == 1'b0) begin
            port_b_fp_in_internal   = converted_b_fp_in;
        end else begin
            port_b_fp_in_internal   = port_b_fp_in;
        end
    end


    // Convert MX-FP Data to FP Data for HBM Prefetch

    generate;
        for (genvar i = 0; i < V_BLOCK_NUM; i++) begin : gen_mxfp_2_fp_convert
            mx_fp_2_fp_block #(
                .BLOCK_DIM          (BLOCK_DIM),
                .MXFP_MANT_WIDTH    (HIGH_MXFP_MANT_WIDTH),
                .MXFP_EXP_WIDTH     (HIGH_MXFP_EXP_WIDTH),
                .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH),
                .FP_MANT_WIDTH      (MANT_WIDTH),
                .FP_EXP_WIDTH       (EXP_WIDTH)
            ) port_b_mx_fp_2_fp_convert (
                .element_in     (port_b_element_in[(i+1)*BLOCK_DIM-1 : i*BLOCK_DIM]),
                .scale_in       (port_b_scale_in[i]),
                .fp_out         (converted_b_fp_in[(i+1)*BLOCK_DIM-1 : i*BLOCK_DIM])
            );
        end
    endgenerate


    // Convert FP Data to MX-FP Data for HBM write
    logic [V_BLOCK_NUM - 1 : 0] high_mxfp_fp_convert_port_b_in_valid;
    logic [V_BLOCK_NUM - 1 : 0] low_mxfp_fp_convert_port_b_in_valid;
    logic [V_BLOCK_NUM - 1 : 0] high_mxfp_fp_convert_port_b_out_ready;
    logic [V_BLOCK_NUM - 1 : 0] high_mxfp_fp_convert_port_b_out_valid;
    logic [V_BLOCK_NUM - 1 : 0] low_mxfp_fp_convert_port_b_out_ready;
    logic [V_BLOCK_NUM - 1 : 0] low_mxfp_fp_convert_port_b_out_valid;


    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            high_mxfp_fp_convert_port_b_in_valid <= '0;
            mxfp_fp_convert_port_b_ready <= 1'b0;
        end else begin
            high_mxfp_fp_convert_port_b_in_valid <= (port_b_mxfp_req == 2'b01) ? {V_BLOCK_NUM{1'b1}} : '0;
            low_mxfp_fp_convert_port_b_in_valid  <= (port_b_mxfp_req  == 2'b10) ? {V_BLOCK_NUM{1'b1}} : '0;
            mxfp_fp_convert_port_b_ready <= 1'b1;
        end
    end

    for (genvar j = 0; j < V_BLOCK_NUM; j++) begin
        fp_2_mx_fp_block #(
            .BLOCK_DIM          (BLOCK_DIM),
            .FP_MANT_WIDTH      (MANT_WIDTH),
            .FP_EXP_WIDTH       (EXP_WIDTH),
            .MXFP_MANT_WIDTH    (HIGH_MXFP_MANT_WIDTH),
            .MXFP_EXP_WIDTH     (HIGH_MXFP_EXP_WIDTH),
            .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH)
        ) fp_2_mx_high_port_b_convert_init(
            .clk(clk),
            .rst(rst),
            .data_in                (port_b_fp_out_internal[(j+1) * BLOCK_DIM - 1 : j * BLOCK_DIM]),
            .data_in_valid          (high_mxfp_fp_convert_port_b_in_valid[j]),
            .data_in_ready          (),
            .element_data_out       (port_b_high_element_out[(j+1) * BLOCK_DIM-1 : j * BLOCK_DIM]),
            .scale_data_out         (port_b_high_scale_out[j]),
            .mx_fp_data_out_valid   (high_mxfp_fp_convert_port_b_out_valid[j]),
            .mx_fp_data_out_ready   (high_mxfp_fp_convert_port_b_out_ready[j])
        );
    end

    for (genvar j = 0; j < V_BLOCK_NUM; j++) begin
        fp_2_mx_fp_block #(
            .BLOCK_DIM          (BLOCK_DIM),
            .FP_MANT_WIDTH      (MANT_WIDTH),
            .FP_EXP_WIDTH       (EXP_WIDTH),
            .MXFP_MANT_WIDTH    (LOW_MXFP_MANT_WIDTH),
            .MXFP_EXP_WIDTH     (LOW_MXFP_EXP_WIDTH),
            .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH)
        ) fp_2_mx_low_port_b_convert_init(
            .clk(clk),
            .rst(rst),
            .data_in                (port_b_fp_out_internal[(j+1) * BLOCK_DIM - 1 : j * BLOCK_DIM]),
            .data_in_valid          (low_mxfp_fp_convert_port_b_in_valid[j]),
            .data_in_ready          (),
            .element_data_out       (port_b_low_element_out[(j+1) * BLOCK_DIM-1 : j * BLOCK_DIM]),
            .scale_data_out         (port_b_low_scale_out[j]),
            .mx_fp_data_out_valid   (low_mxfp_fp_convert_port_b_out_valid[j]),
            .mx_fp_data_out_ready   (low_mxfp_fp_convert_port_b_out_ready[j])
        );
    end

    join_n #(
        .NUM_HANDSHAKES(V_BLOCK_NUM)
    ) high_mxfp_fp_convert_join (
        .data_in_valid(high_mxfp_fp_convert_port_b_out_valid),
        .data_in_ready(high_mxfp_fp_convert_port_b_out_ready),
        .data_out_valid(port_b_mxfp_high_out_valid),
        .data_out_ready(mxfp_fp_convert_port_b_ready)
    );

    join_n #(
        .NUM_HANDSHAKES(V_BLOCK_NUM)
    ) low_mxfp_fp_convert_low_join (
        .data_in_valid(low_mxfp_fp_convert_port_b_out_valid),
        .data_in_ready(low_mxfp_fp_convert_port_b_out_ready),
        .data_out_valid(port_b_mxfp_low_out_valid),
        .data_out_ready(mxfp_fp_convert_port_b_ready)
    );

// -----------------------------
// Storage 
// -----------------------------

    prim_generic_ram_2p #(
        .Width((EXP_WIDTH + MANT_WIDTH + 1) * VLEN),
        .Depth(SRAM_DEPTH),
        .DataBitsPerMask((EXP_WIDTH + MANT_WIDTH + 1))
        `ifdef SIMULATION
        ,
        .ResultFile(MEM_RESULT_FILE)
        `endif
    ) element_storage (
        .clk_i(clk),

        .a_req_i        (port_a_req),
        .a_write_i      (port_a_write_en),
        .a_addr_i       (translated_port_a_addr_internal),
        .a_wdata_i      (port_a_fp_in_internal),
        .a_wmask_i      (port_a_mask_in),
        .a_rdata_o      (port_a_fp_out_internal),

        .b_req_i        (port_b_req || port_b_mxfp_req),
        .b_write_i      (port_b_write_en),
        .b_addr_i       (translated_port_b_addr),
        .b_wdata_i      (port_b_fp_in_internal),
        .b_wmask_i      (port_b_mask_in),
        .b_rdata_o      (port_b_fp_out_internal),
        // Unused
        .cfg_i('0),
        .cfg_rsp_o()
    );


endmodule