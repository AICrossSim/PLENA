`timescale 1ns / 1ps
// Copyright lowRISC contributors (OpenTitan project).
// Licensed under the Apache License, Version 2.0, see LICENSE for details.
// SPDX-License-Identifier: Apache-2.0
//
// Synchronous dual-port SRAM register model
//   This module is for simulation and small size SRAM.
//   Implementing ECC should be done inside wrapper not this model.
`include "prim_assert.sv"
`include "prim_ram_2p_pkg.svh"
module prim_generic_ram_2p import prim_ram_2p_pkg::*; #(
  parameter  int Width           = 32, // bit
  parameter  int Depth           = 128,
  parameter  int DataBitsPerMask = 1, // Number of data bits per bit of write mask
  `ifdef SIMULATION
    parameter  string    MemInitFile     = "", 
    parameter  string    ResultFile      = "",
  `endif
  localparam int Aw              = $clog2(Depth),  // derived parameter
  localparam int MaskWidth = Width / DataBitsPerMask
) (
  input clk_i,

  input                    a_req_i,
  input                    a_write_i,
  input        [Aw-1:0]    a_addr_i,
  input        [Width-1:0] a_wdata_i,
  input  logic [MaskWidth-1:0] a_wmask_i,
  output logic [Width-1:0] a_rdata_o,

  input                    b_req_i,
  input                    b_write_i,
  input        [Aw-1:0]    b_addr_i,
  input        [Width-1:0] b_wdata_i,
  input  logic [MaskWidth-1:0] b_wmask_i,
  output logic [Width-1:0] b_rdata_o,

  input  ram_2p_cfg_t      cfg_i,
  output ram_2p_cfg_rsp_t  cfg_rsp_o
);

// For certain synthesis experiments we compile the design with generic models to get an unmapped
// netlist (GTECH). In these synthesis experiments, we typically black-box the memory models since
// these are going to be simulated using plain RTL models in netlist simulations. This can be done
// by analyzing and elaborating the design, and then removing the memory submodules before writing
// out the verilog netlist. However, memory arrays can take a long time to elaborate, and in case
// of dual port rams they can even trigger elab errors due to multiple processes writing to the
// same memory variable concurrently. To this end, we exclude the entire logic in this module in
// these runs with the following macro.
`ifndef SYNTHESIS_MEMORY_BLACK_BOXING

  logic unused_cfg;
  assign unused_cfg = ^cfg_i;
  assign cfg_rsp_o  = '0;

  // Width of internal write mask. Note *_wmask_i input into the module is always assumed
  // to be the full bit mask.


  logic [Width-1:0]     mem [Depth];
  logic [MaskWidth-1:0] a_wmask;
  logic [MaskWidth-1:0] b_wmask;

  // for (genvar k = 0; k < MaskWidth; k++) begin : gen_wmask
  //   assign a_wmask[k] = &a_wmask_i[k*DataBitsPerMask +: DataBitsPerMask];
  //   assign b_wmask[k] = &b_wmask_i[k*DataBitsPerMask +: DataBitsPerMask];

  //   // Ensure that all mask bits within a group have the same value for a write
  //   `ASSERT(MaskCheckPortA_A, a_req_i && a_write_i |->
  //       a_wmask_i[k*DataBitsPerMask +: DataBitsPerMask] inside {{DataBitsPerMask{1'b1}}, '0},
  //       clk_a_i, '0)
  //   `ASSERT(MaskCheckPortB_A, b_req_i && b_write_i |->
  //       b_wmask_i[k*DataBitsPerMask +: DataBitsPerMask] inside {{DataBitsPerMask{1'b1}}, '0},
  //       clk_b_i, '0)
  // end
  assign a_wmask = a_wmask_i;
  assign b_wmask = b_wmask_i;

  // Xilinx FPGA specific Dual-port RAM coding style
  // using always instead of always_ff to avoid 'ICPD  - illegal combination of drivers' error
  // thrown due to 'mem' being driven by two always processes below
  logic conflict;
  assign conflict = a_req_i && a_write_i && b_req_i && b_write_i && (a_addr_i == b_addr_i);

  always @(posedge clk_i) begin
    // READS
    if (a_req_i && !a_write_i) begin
      a_rdata_o <= mem[a_addr_i];
    end
    if (b_req_i && !b_write_i) begin
      b_rdata_o <= mem[b_addr_i];
    end

    // ADDRESS CONFLICT DETECTION

    // WRITES
    if (!conflict) begin
      if (a_req_i && a_write_i) begin
        for (int i = 0; i < MaskWidth; i++) begin
          if (a_wmask[i]) begin
            mem[a_addr_i][i*DataBitsPerMask +: DataBitsPerMask] <=
              a_wdata_i[i*DataBitsPerMask +: DataBitsPerMask];
          end
        end
      end

      if (b_req_i && b_write_i) begin
        for (int i = 0; i < MaskWidth; i++) begin
          if (b_wmask[i]) begin
            mem[b_addr_i][i*DataBitsPerMask +: DataBitsPerMask] <=
              b_wdata_i[i*DataBitsPerMask +: DataBitsPerMask];
          end
        end
      end
    end else begin
      // TODO: 
    end
  end


  `include "prim_util_memload.svh"
  
`ifdef SIMULATION
    final begin
        if (ResultFile != "") begin
            string result_filename;
            $sformat(result_filename, "%s", ResultFile);
            $display("Writing result file from: %s", result_filename);
            $writememh(result_filename, mem);
        end
    end
`endif

`endif
endmodule