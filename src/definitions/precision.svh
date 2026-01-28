`ifndef PRECISION_SVH
`define PRECISION_SVH

/*
Module      : Definitions for Precision
Description :
            : Here we assume KV precision is less or equal to WT precision.
*/


package precision_pkg;
    // HBM Storage Precision
    // Matrix machine uses integer MAC with 8-bit mantissa for DSP inference
    // Element width: 8 (mant) + 5 (exp) + 1 (sign) = 14 bits
    localparam   ACT_MXFP_MANT_WIDTH = 8;  // 8-bit for DSP inference (9x9 signed multiply)
    localparam   ACT_MXFP_EXP_WIDTH  = 5;
    localparam   KV_MX_MANT_WIDTH    = 8;  // 8-bit for DSP inference
    localparam   KV_MX_EXP_WIDTH     = 5;
    localparam   KV_MX_INT_ENABLE    = 0;  // Currently not used
    localparam   WT_MX_MANT_WIDTH    = 8;  // 8-bit for DSP inference
    localparam   WT_MX_EXP_WIDTH     = 5;
    localparam   WT_MX_INT_ENABLE    = 1;  // Enable integer MAC for DSP inference
    localparam   MX_SCALE_WIDTH      = 8;

    localparam   BLOCK_DIM = 8;
    // Per Unit Precision (Reduced from 15-bit to 9-bit mantissa for LUT savings)
    // Must be >= 8-bit mantissa for conversion module compatibility
    localparam   V_FP_EXP_WIDTH  = 8;  // Keep 8 for conversion module compatibility
    localparam   V_FP_MANT_WIDTH = 8;  // Reduced from 15 (saves ~40% LUTs per ALU)
    localparam   M_FP_EXP_WIDTH  = 8;
    localparam   M_FP_MANT_WIDTH = 9;
    localparam   S_FP_EXP_WIDTH  = 8;
    localparam   S_FP_MANT_WIDTH = 9;
    localparam   INT_DATA_WIDTH  = 32;
    // Compute Related Precision
    localparam   PRODUCT_EXT_EXP_WIDTH       = 0;
    localparam   PRODUCT_EXT_MANT_WIDTH      = 1;
    localparam   BLOCK_ADD_EXT_EXP_WIDTH     = 1;
    localparam   BLOCK_ADD_EXT_MANT_WIDTH    = 1;
    localparam   FP_ADD_EXT_EXP_WIDTH        = 1;
    localparam   FP_ADD_EXT_MANT_WIDTH       = 1;
    localparam   ROUND_FP_EXP_WIDTH          = 5;
    localparam   ROUND_FP_MANT_WIDTH         = 8;
endpackage

`endif