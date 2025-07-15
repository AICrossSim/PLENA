`ifndef PRECISION_SVH
`define PRECISION_SVH

/*
Module      : Definitions for Precision
Description : 
            : Here we assume KV precision is less or equal to WT precision.
*/


package precision_pkg;
    parameter   ACT_MXFP_MANT_WIDTH             = 3;
    parameter   ACT_MXFP_EXP_WIDTH              = 4;
    parameter   KV_MXFP_MANT_WIDTH              = 3;
    parameter   KV_MXFP_EXP_WIDTH               = 4;
    parameter   WT_MXFP_MANT_WIDTH              = 3;
    parameter   WT_MXFP_EXP_WIDTH               = 4;
    parameter   MXFP_SCALE_WIDTH                = 8;
    parameter   BLOCK_DIM                       = 4;
    parameter   V_FP_EXP_WIDTH                  = 7;
    parameter   V_FP_MANT_WIDTH                 = 8;
    parameter   M_FP_EXP_WIDTH                  = 8;
    parameter   M_FP_MANT_WIDTH                 = 23;
    parameter   S_FP_EXP_WIDTH                  = 7;
    parameter   S_FP_MANT_WIDTH                 = 8;
    parameter   INT_DATA_WIDTH                = 32;
    parameter   PRODUCT_EXT_EXP_WIDTH           = 0;
    parameter   PRODUCT_EXT_MANT_WIDTH          = 0;
    parameter   BLOCK_ADD_EXT_EXP_WIDTH         = 1;
    parameter   BLOCK_ADD_EXT_MANT_WIDTH        = 0;
    parameter   FP_ADD_EXT_EXP_WIDTH            = 1;
    parameter   FP_ADD_EXT_MANT_WIDTH           = 0;
    parameter   ROUND_FP_EXP_WIDTH              = 4;
    parameter   ROUND_FP_MANT_WIDTH             = 3; 
endpackage

`endif