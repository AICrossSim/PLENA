`ifndef PRECISION_SVH
`define PRECISION_SVH

package precision_pkg;

    parameter   MXFP_MANT_WIDTH                 = 8;
    parameter   MXFP_EXP_WIDTH                  = 4;
    parameter   MXFP_SCALE_WIDTH                = 8;
    parameter   BLOCK_DIM                       = 4;
    parameter   FP_EXP_WIDTH                    = 5;
    parameter   FP_MANT_WIDTH                   = 10;
    parameter   FIXED_DATA_WIDTH                = 32;
    parameter   PRODUCT_EXT_EXP_WIDTH           = 1;
    parameter   PRODUCT_EXT_MANT_WIDTH          = 0;
    parameter   BLOCK_ADD_EXT_EXP_WIDTH         = 1;
    parameter   BLOCK_ADD_EXT_MANT_WIDTH        = 0;
    parameter   FP_ADD_EXT_EXP_WIDTH            = 1;
    parameter   FP_ADD_EXT_MANT_WIDTH           = 0;
    parameter   ROUND_FP_EN                     = 0;
    parameter   ROUND_FP_EXP_WIDTH              = 4;
    parameter   ROUND_FP_MANT_WIDTH             = 3; 

endpackage

`endif