`timescale 1ns / 1ps
`include "tl_util.svh"

/*
Module      : TileLink master
Description : 
  - TL-UL (TileLink Uncached Lite) master interface
  - Supports simple read (Get) and write (PutFullData) operations
  - Fetches data through TileLink and outputs it with valid strobe
*/

module tl_master #(
  parameter int DataWidth = 32,
  parameter int AddrWidth = 32,
  parameter int SourceWidth = 1,
  parameter int SinkWidth = 1,
  localparam int MASK_WIDTH = DataWidth / 8
)(
  input  logic clk,
  input  logic rst,

  // Control signals
  input  logic req_en,
  input  logic [AddrWidth-1:0] addr,
  output logic [DataWidth-1:0] fetch_data,

  input  logic write_en,
  input  logic [MASK_WIDTH-1:0] write_mask,
  input  logic [DataWidth-1:0] write_data,

  // Status Indicators
  output logic fetch_data_valid,
  // output logic write_data_complete,

  `TL_DECLARE_HOST_PORT(DataWidth, AddrWidth, SourceWidth, SinkWidth, host)
);

  import tl_pkg::*;

  `TL_DECLARE(DataWidth, AddrWidth, SourceWidth, SinkWidth, host);
  `TL_BIND_HOST_PORT(host, host);

  // Disable unused channels
  // assign host_b_valid = 1'b0;
  // assign host_b    = 'x;
  // assign host_c_ready = 1'b1;
  // assign host_e_ready = 1'b1;

  typedef enum logic [1:0] {
    IDLE, SEND_REQ, WAIT_RESP
  } state_t;

  state_t state, next_state;
  tl_a_op_e next_a_opcode;
  logic [AddrWidth-1:0] next_addr;
  logic [DataWidth-1:0] next_wdata;

  // Output registers
  logic [DataWidth-1:0] r_fetch_data;
  logic r_fetch_data_valid;

  assign fetch_data = r_fetch_data;
  assign fetch_data_valid = r_fetch_data_valid;

  // FSM State register
  always_ff @(posedge clk or posedge rst) begin
    if (rst) begin
      state <= IDLE;
      r_fetch_data <= '0;
      r_fetch_data_valid <= 1'b0;
    end else begin
      state <= next_state;
      if (host_d_valid && host_d.opcode == AccessAckData) begin // AccessAckData
        r_fetch_data <= host_d.data;
        r_fetch_data_valid <= 1'b1;
      end else if (host_d.opcode == AccessAck) begin
        r_fetch_data_valid <= 1'b0;
      end else begin
        r_fetch_data_valid <= 1'b0;
      end
    end
  end


  logic fetch_in_progress;

  // FSM combinational logic
  always_comb begin
    if (rst) begin
      next_state = IDLE;
      fetch_in_progress = 1'b0;
    end else begin
      if (req_en) begin
          fetch_in_progress = 1'b1;
      end else if (host_d_valid && host_d.opcode == AccessAckData) begin // AccessAckData
          fetch_in_progress = 1'b0;
      end

      host_d_ready  = fetch_in_progress;
      host_a.mask    = write_mask;
      // next_state = state;
      case (state)
        IDLE: begin
          host_a_valid   = 1'b0;
          if (req_en) begin
            if (write_en) begin
              next_a_opcode = PutFullData; // PutFullData
              next_addr   = addr;
              next_wdata  = write_data;
              next_state  = SEND_REQ;
            end else begin
              next_a_opcode = Get; // Get
              next_addr   = addr;
              next_state  = SEND_REQ;
            end
          end 
        end

        SEND_REQ: begin
          host_a_valid   = 1'b1;
          host_a.opcode  = next_a_opcode;
          host_a.address = next_addr;
          if (next_a_opcode == PutFullData) begin // PutFullData
            host_a.data = next_wdata;
          end
          if (host_a_ready) begin
            next_state = WAIT_RESP;
          end
        end

        WAIT_RESP: begin
          host_a_valid   = 1'b0;
          if (host_d_valid) begin
            next_state = IDLE;
          end
        end

        default: begin
          // Default TileLink signals
          host_a_valid   = 1'b0;
          host_a.opcode  = PutFullData;
          host_a.param   = 3'b000;
          host_a.size    = 3'b110; // 4 bytes
          host_a.source  = '0;
          host_a.address = '0;
          host_a.data    = '0;
          next_state     = IDLE;
        end
      endcase
    end
  end
endmodule
