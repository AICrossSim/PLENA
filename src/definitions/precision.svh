`ifdef PRECISION_SVH
`define PRECISION_SVH


parameter   MXFP_MANT_WIDTH   = 8;
parameter   MXFP_EXP_WIDTH    = 4;
parameter   MX_FP_SCALE_WIDTH = 8;


parameter   BLOCK_DIM         = 4,
parameter   BLOCK_NUM         = MLEN / BLOCK_DIM,


parameter   PRODUCT_EXT_EXP_WIDTH           = 1;
parameter   PRODUCT_EXT_MANT_WIDTH          = 0;
parameter   BLOCK_ADD_EXT_EXP_WIDTH         = 1;  // Note: this param control precision for both blockwise addition within adder tree and the blockwise adder
parameter   BLOCK_ADD_EXT_MANT_WIDTH        = 0;
parameter   FP_ADD_EXT_EXP_WIDTH            = 1;
parameter   FP_ADD_EXT_MANT_WIDTH           = 0;

parameter   ROUND_FP_EN            = 0;
parameter   ROUND_FP_EXP_WIDTH     = 4;
parameter   ROUND_FP_MANT_WIDTH    = 3; 


`endif