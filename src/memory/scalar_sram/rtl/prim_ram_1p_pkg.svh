`ifndef PRIM_RAM_1P_PKG_SVH
`define PRIM_RAM_1P_PKG_SVH
// Copyright lowRISC contributors (OpenTitan project).
// Licensed under the Apache License, Version 2.0, see LICENSE for details.
// SPDX-License-Identifier: Apache-2.0
//
`timescale 1ns / 1ps
package prim_ram_1p_pkg;

  typedef struct packed {
    logic       test;
    logic       cfg_en;
    logic [3:0] cfg;
  } cfg_t;

  typedef struct packed {
    cfg_t ram_cfg;  // configuration for ram
    cfg_t rf_cfg;   // configuration for regfile
  } ram_1p_cfg_t;

  typedef struct packed {
    logic done;
  } ram_1p_cfg_rsp_t;

  parameter ram_1p_cfg_t RAM_1P_CFG_DEFAULT = '0;

endpackage // prim_ram_1p_pkg

 `endif