`ifndef PRECISION_SVH
`define PRECISION_SVH

/*
Module      : Definitions for Precision
Description :
            : Here we assume KV precision is less or equal to WT precision.
*/


package precision_pkg;
    // HBM Storage Precision (Higher precision for DSP inference experiment)
    // Element width: 8 (mant) + 5 (exp) + 1 (sign) = 14 bits
    // 8x8 = 16-bit products should be more suitable for DSP48E1
    localparam   ACT_MXFP_MANT_WIDTH = 8;  // Increased from 4 for DSP inference
    localparam   ACT_MXFP_EXP_WIDTH  = 5;  // Keep same
    localparam   KV_MX_MANT_WIDTH    = 8;  // Increased from 4 for DSP inference
    localparam   KV_MX_EXP_WIDTH     = 5;  // Keep same
    localparam   KV_MX_INT_ENABLE    = 0;  // Currently not used.
    localparam   WT_MX_MANT_WIDTH    = 8;  // Increased from 4 for DSP inference
    localparam   WT_MX_EXP_WIDTH     = 5;  // Keep same
    localparam   WT_MX_INT_ENABLE    = 1;  // Re-enabled with keep attributes to prevent optimization
    localparam   MX_SCALE_WIDTH      = 8;

    localparam   BLOCK_DIM = 8;
    // Per Unit Precision (Accumulator/Output precision - widened for 8-bit mantissa inputs)
    localparam   V_FP_EXP_WIDTH  = 8;  // Increased from 6 for wider accumulator
    localparam   V_FP_MANT_WIDTH = 15; // Increased from 5 for 8x8=16-bit products + accumulation
    localparam   M_FP_EXP_WIDTH  = 8;  // Increased from 6
    localparam   M_FP_MANT_WIDTH = 15; // Increased from 5
    localparam   S_FP_EXP_WIDTH  = 8;  // Increased from 6
    localparam   S_FP_MANT_WIDTH = 15; // Increased from 5
    localparam   INT_DATA_WIDTH  = 32;
    // Compute Related Precision (Extended precision for intermediate results)
    localparam   PRODUCT_EXT_EXP_WIDTH       = 0;  // Keep original
    localparam   PRODUCT_EXT_MANT_WIDTH      = 1;  // Keep minimal guard bits
    localparam   BLOCK_ADD_EXT_EXP_WIDTH     = 1;  // Keep original
    localparam   BLOCK_ADD_EXT_MANT_WIDTH    = 1;  // Keep minimal guard bits
    localparam   FP_ADD_EXT_EXP_WIDTH        = 1;  // Keep original
    localparam   FP_ADD_EXT_MANT_WIDTH       = 1;  // Keep minimal guard bits
    localparam   ROUND_FP_EXP_WIDTH          = 5;  // Match input exp width
    localparam   ROUND_FP_MANT_WIDTH         = 8;  // Match input mant width
endpackage

`endif