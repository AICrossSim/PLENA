`ifndef PRECISION_SVH
`define PRECISION_SVH

/*
Module      : Definitions for Precision
Description : 
            : Here we assume KV precision is less or equal to WT precision.
*/


package precision_pkg;
    // HBM Storage Precision 
    parameter   ACT_MXFP_MANT_WIDTH = 3;
    parameter   ACT_MXFP_EXP_WIDTH  = 4;
    parameter   KV_MX_MANT_WIDTH    = 2;
    parameter   KV_MX_EXP_WIDTH     = 1;
    parameter   KV_MX_INT_ENABLE    = 0;    // Currently not used.
    parameter   WT_MX_MANT_WIDTH    = 2;
    parameter   WT_MX_EXP_WIDTH     = 1;
    parameter   WT_MX_INT_ENABLE    = 0;
    parameter   MX_SCALE_WIDTH      = 8;
    
    parameter   BLOCK_DIM = 8;
    // Per Unit Precision
    parameter   V_FP_EXP_WIDTH  = 6;
    parameter   V_FP_MANT_WIDTH = 5;
    parameter   M_FP_EXP_WIDTH  = 6;
    parameter   M_FP_MANT_WIDTH = 5;
    parameter   S_FP_EXP_WIDTH  = 6;
    parameter   S_FP_MANT_WIDTH = 5;
    parameter   INT_DATA_WIDTH  = 32;
    // Compute Related Precision
    parameter   PRODUCT_EXT_EXP_WIDTH       = 0;
    parameter   PRODUCT_EXT_MANT_WIDTH      = 0;
    parameter   BLOCK_ADD_EXT_EXP_WIDTH     = 1;
    parameter   BLOCK_ADD_EXT_MANT_WIDTH    = 0;
    parameter   FP_ADD_EXT_EXP_WIDTH        = 1;
    parameter   FP_ADD_EXT_MANT_WIDTH       = 0;
    parameter   ROUND_FP_EXP_WIDTH          = 4;
    parameter   ROUND_FP_MANT_WIDTH         = 3;
endpackage

`endif