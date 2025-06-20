`timescale 1ns/1ps

/*
Module      : Top Level SRAM design for scratchpad
Timing      : Sequential Logic, 1 cycle for read/write process.
Description :
            : This module supports two port reading
            : The addressing mode is Little Endian.
            : Port A ->  R: Matrix Multiplicand Vector or Vector Operand (RS1)               W: Vector Result from either Matrix or Vector Machine, 
            : Port B ->  R: Matrix Offest Vector or Vector Operand (RS2) or HBM Write Data   W: Vector Prefetch
Status      :
*/

module fp_vector_sram #(
    
    // MX-FP Data Format
    parameter MXFP_EXP_WIDTH    = 4,
    parameter MXFP_MANT_WIDTH   = 3,
    parameter MXFP_SCALE_WIDTH  = 8,
    // FP Data Format
    parameter   EXP_WIDTH         = 8,                                  
    parameter   MANT_WIDTH        = 7,

    // Dimension
    parameter   VLEN              = 8,   
    parameter   MLEN              = 8, 
    parameter   BLOCK_DIM         = 4,                                
    localparam  BLOCK_NUM         = VLEN / BLOCK_DIM,

    // SRAM
    parameter   SRAM_DEPTH          = 128,
    parameter   ON_CHIP_ADDR_WIDTH  = 32,
    parameter   PREFETCH_AMOUNT     = 4,
    // For Debugging
    parameter string MEM_RESULT_FILE = ""

)(
    input   logic clk,
    input   logic rst,

    // Port A
    input   logic port_a_req,
    input   logic port_a_write_en,
    input   logic [ON_CHIP_ADDR_WIDTH - 1 : 0] port_a_addr,
    input   logic control, // 0 for Vector Machine, 1 for Matrix Machine
    // FP Data Connection
    input   logic [VLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0]    port_a_v_fp_in,
    input   logic [MLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0]    port_a_m_fp_in,
    input   logic [VLEN - 1 : 0]                                        port_a_mask_in,
    output  logic [VLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0]    port_a_v_fp_out,
    output  logic [MLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0]    port_a_m_fp_out,
    // // MX-FP Connection
    // output  logic [VLEN - 1 : 0]        [MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]      port_a_element_out,
    // output  logic [BLOCK_NUM - 1 : 0]   [MXFP_SCALE_WIDTH - 1 : 0]                  port_a_scale_out,

    // Port B
    input   logic port_b_req,
    input   logic port_b_write_en,
    input   logic [ON_CHIP_ADDR_WIDTH - 1 : 0] port_b_addr,
    // FP Data Connection
    output  logic [VLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0]                port_b_fp_out,
    input   logic [VLEN - 1 : 0]                                                    port_b_mask_in,
    // MX-FP Connection
    input   logic [VLEN - 1 : 0]        [MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]      port_b_element_in,
    input   logic [BLOCK_NUM - 1 : 0]   [MXFP_SCALE_WIDTH - 1 : 0]                  port_b_scale_in,
    output  logic port_b_mxfp_out_valid,

    output  logic [VLEN - 1 : 0]        [MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]      port_b_element_out,
    output  logic [BLOCK_NUM - 1 : 0]   [MXFP_SCALE_WIDTH - 1 : 0]                  port_b_scale_out,

    // Status Tracking for Prefetch
    input   logic prefetch_en,
    input   logic [ON_CHIP_ADDR_WIDTH - 1 : 0] prefetch_addr,
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
    logic [VLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0] port_b_fp_out_internal;
    localparam int REPL_COUNT = (VLEN - MLEN) * (EXP_WIDTH + MANT_WIDTH + 1);
    
    // -----------------------------
    // Prefetch Tag Tracking
    // -----------------------------

    // Tag Matching, trackinng the prefetch status.
    logic [INTERNAL_ADDR_LEN - 1 : 0]     translated_port_b_addr, translated_port_a_addr, translated_prefetch_addr;
    logic [SRAM_DEPTH - 1 : 0]            mem_data_tag;
    
    localparam BITWIDTH_PER_ROW =  (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) * VLEN / 8;
    assign translated_port_a_addr = port_a_addr >> $clog2(BITWIDTH_PER_ROW);
    assign translated_port_b_addr = port_b_addr >> $clog2(BITWIDTH_PER_ROW);
    assign translated_prefetch_addr = prefetch_addr >> $clog2(BITWIDTH_PER_ROW);

    always_ff @(posedge clk) begin
        if (rst) begin
            mem_data_tag <= {{SRAM_DEPTH{1'b1}}};
        end else if (prefetch_en) begin
            for (int i = translated_prefetch_addr; i < translated_prefetch_addr + PREFETCH_AMOUNT; i++) begin
                mem_data_tag[i] <= 1'b0;
            end
        end else if (port_b_write_en) begin
            mem_data_tag[translated_port_b_addr] <= 1'b1;
        end
    end

    assign data_not_ready =     (port_b_req & !port_b_write_en) & (mem_data_tag[translated_port_b_addr] == 1'b0)
                            ||  (port_a_req & !port_a_write_en) & (mem_data_tag[translated_port_a_addr] == 1'b0);   

    // -----------------------------
    // Port A Management
    // -----------------------------

    always_comb begin
        if (control == 1'b0) begin
            // Vector Machine Mode
            port_a_fp_in_internal = port_a_v_fp_in;
            port_a_v_fp_out = port_a_fp_out_internal;
        end else begin
            // Matrix Machine Mode
            port_a_fp_in_internal = {{REPL_COUNT{1'b0}}, port_a_m_fp_in}; // Use Matrix FP Input
            port_a_m_fp_out = port_a_fp_out_internal[VLEN - 1:0]; // Ensure the output is within VLEN
        end
    end


    // -----------------------------
    // Port B Management
    // -----------------------------
    
    assign port_b_fp_out = port_b_fp_out_internal;

    // Convert MX-FP Data to FP Data for HBM Prefetch
    logic [VLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0]    converted_b_fp_in;
    logic [VLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0]    converted_b_fp_out;
    generate;
        for (genvar i = 0; i < BLOCK_NUM; i++) begin : gen_mxfp_2_fp_convert
            mx_fp_2_fp_block #(
                .BLOCK_DIM          (BLOCK_DIM),
                .MXFP_MANT_WIDTH    (MXFP_MANT_WIDTH),
                .MXFP_EXP_WIDTH     (MXFP_EXP_WIDTH),
                .FP_MANT_WIDTH      (MANT_WIDTH),
                .FP_EXP_WIDTH       (EXP_WIDTH)
            ) mx_fp_2_fp_convert (
                .element_in     (port_b_element_in[(i+1)*BLOCK_DIM-1 : i*BLOCK_DIM]),
                .scale_in       (port_b_scale_in[i]),
                .fp_out         (converted_b_fp_in[(i+1)*BLOCK_DIM-1 : i*BLOCK_DIM])
            );
        end
    endgenerate


    // Convert FP Data to MX-FP Data for HBM write
    logic [BLOCK_NUM - 1 : 0] mxfp_fp_convert_port_b_in_valid;
    logic [BLOCK_NUM - 1 : 0] mxfp_fp_convert_port_b_out_ready;
    logic [BLOCK_NUM - 1 : 0] mxfp_fp_convert_port_b_out_valid;
    logic mxfp_fp_convert_ready;
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            mxfp_fp_convert_port_b_in_valid <= '0;
            mxfp_fp_convert_ready <= 1'b0;
        end else begin
            mxfp_fp_convert_port_b_in_valid <= port_b_req ? {BLOCK_NUM{1'b1}} : '0;
            mxfp_fp_convert_ready <= 1'b1;
        end
    end

    for (genvar j = 0; j < BLOCK_NUM; j++) begin
        fp_2_mx_fp_block #(
            .BLOCK_DIM          (BLOCK_DIM),
            .FP_MANT_WIDTH      (MANT_WIDTH),
            .FP_EXP_WIDTH       (EXP_WIDTH),
            .MXFP_MANT_WIDTH    (MXFP_MANT_WIDTH),
            .MXFP_EXP_WIDTH     (MXFP_EXP_WIDTH),
            .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH)
        ) fp_2_mx_port_b_convert_init(
            .clk(clk),
            .rst(rst),
            .data_in(port_b_fp_out_internal[(j+1) * BLOCK_DIM - 1 : j * BLOCK_DIM]),
            .data_in_valid(mxfp_fp_convert_port_b_in_valid),
            .data_in_ready(),
            .element_data_out(port_b_element_out[(j+1) * BLOCK_DIM-1 : j * BLOCK_DIM]),
            .scale_data_out(port_b_scale_out[j]),
            .mx_fp_data_out_valid(mxfp_fp_convert_port_b_out_valid[j]),
            .mx_fp_data_out_ready(mxfp_fp_convert_port_b_out_ready[j])
        );
    end

    join_n #(
        .NUM_HANDSHAKES(BLOCK_NUM)
    ) mxfp_fp_convert_join (
        .data_in_valid(mxfp_fp_convert_port_b_out_valid),
        .data_in_ready(mxfp_fp_convert_port_b_out_ready),
        .data_out_valid(port_b_mxfp_out_valid),
        .data_out_ready(mxfp_fp_convert_ready)
    );

// Main Storage in FP format
prim_generic_ram_2p #(
    .Width((EXP_WIDTH + MANT_WIDTH + 1) * VLEN),
    .Depth(SRAM_DEPTH),
    .DataBitsPerMask((EXP_WIDTH + MANT_WIDTH + 1)),
    .ResultFile(MEM_RESULT_FILE)
) element_storage (
    .clk_a_i(clk),
    .clk_b_i(clk),

    .a_req_i        (port_a_req),
    .a_write_i      (port_a_write_en),
    .a_addr_i       (translated_port_a_addr),
    .a_wdata_i      (port_a_fp_in_internal),
    .a_wmask_i      (port_a_mask_in),
    .a_rdata_o      (port_a_fp_out_internal),

    .b_req_i        (port_b_req),
    .b_write_i      (port_b_write_en),
    .b_addr_i       (translated_port_b_addr),
    .b_wdata_i      (converted_b_fp_in),
    .b_wmask_i      (port_b_mask_in),
    .b_rdata_o      (port_b_fp_out_internal),
    // Unused
    .cfg_i('0),
    .cfg_rsp_o()
);


endmodule