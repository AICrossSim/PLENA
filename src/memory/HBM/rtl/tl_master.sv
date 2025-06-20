`timescale 1ns / 1ps
`include "tl_util.svh"

/*
Module      : TileLink master
Description : 
  - TL-UL (TileLink Uncached Lite) master interface
  - Supports simple read (Get) and write (PutFullData) operations
  - Fetches data through TileLink and outputs it with valid
  - Note that, the req and addr only need to be valid for one cycle
*/

module tl_master #(
  parameter int DataWidth = 32,
  parameter int AddrWidth = 32,
  parameter int SourceWidth = 1,
  parameter int SinkWidth = 1,
  parameter int LOAD_AMOUNT = 1, 
  parameter int WRITE_AMOUNT = 1,
  localparam int MASK_WIDTH = DataWidth / 8
)(
  input  logic clk,
  input  logic rst,

  // Control signals
  input  logic req_en,
  input  logic [AddrWidth-1:0] addr,
  output logic [DataWidth-1:0] fetch_data,
  input  logic fetch_data_ready,

  input  logic write_en,
  input  logic [MASK_WIDTH-1:0] write_mask,
  input  logic [DataWidth-1:0] write_data,

  // Status Indicators
  output logic fetch_data_valid,
  output logic complete_fetch,
  output logic ready_to_write,

  `TL_DECLARE_HOST_PORT(DataWidth, AddrWidth, SourceWidth, SinkWidth, host)
);

  localparam WRITE_SIZE = $clog2(DataWidth / 8);
  import tl_pkg::*;

  `TL_DECLARE(DataWidth, AddrWidth, SourceWidth, SinkWidth, host);
  `TL_BIND_HOST_PORT(host, host);

  typedef enum logic [1:0] {
    IDLE, SEND_RREQ, SEND_WREQ, WAIT_RESP
  } state_t;

  state_t state, next_state, previous_state;
  tl_a_op_e next_a_opcode;
  logic [AddrWidth-1:0] next_addr;
  logic [DataWidth-1:0] next_wdata;

  // Output registers
  logic [DataWidth-1:0] r_fetch_data;
  logic r_fetch_data_valid;

  assign fetch_data = r_fetch_data;
  assign fetch_data_valid = r_fetch_data_valid;

  // Continuous Loading
  int continuous_prefetch_counter;
  int continuous_write_counter;
  logic previous_d_valid;

  assign ready_to_write = host_a_ready;
  // FSM State register
  always_ff @(posedge clk or posedge rst) begin
    if (rst) begin
      state <= IDLE;
      previous_state <= IDLE;
      r_fetch_data <= '0;
      r_fetch_data_valid <= 1'b0;
      continuous_prefetch_counter <= 0;
      previous_d_valid <= 1'b0;
    end else begin
      previous_state <= state;
      state <= next_state;
      previous_d_valid <= host_d_valid;

      if (host_d_valid && host_d.opcode == AccessAckData) begin // AccessAckData
        r_fetch_data <= host_d.data;
        r_fetch_data_valid <= 1'b1;
      end else if (host_d.opcode == AccessAck) begin
        r_fetch_data_valid <= 1'b0;
      end else begin
        r_fetch_data_valid <= 1'b0;
      end

      // Increment the continuous prefetch counter
      if (state == SEND_RREQ && next_state == WAIT_RESP) begin
        continuous_prefetch_counter <= 0; // Reset counter when waiting for response
      end else if (state == SEND_RREQ && host_a_ready) begin
        continuous_prefetch_counter <= continuous_prefetch_counter + 1;
      end else if (state == IDLE) begin
        continuous_prefetch_counter <= 0; // Reset counter when idle
      end

      // Increment the continuous write counter
      if (state == SEND_WREQ && write_en && host_a_ready) begin
        continuous_write_counter <= continuous_write_counter + 1;
      end else if (state == IDLE) begin
        continuous_write_counter <= 0; // Reset counter when idle
      end
    end
  end

  assign complete_fetch =  (previous_d_valid == 1'b1 && host_d_valid == 1'b0);
  
  // FSM combinational logic
  always_comb begin
      host_d_ready    = fetch_data_ready;
      host_a.mask     = write_mask;
      case (state)
        IDLE: begin
          host_a_valid   = 1'b0;
          if (req_en) begin
            next_a_opcode = Get; // Get
            next_addr   = addr;
            next_state  = SEND_RREQ;
          end else if (write_en) begin
            next_a_opcode = PutFullData;
            next_addr   = addr;
            next_wdata  = write_data;
            next_state  = SEND_WREQ;
          end else begin
            next_a_opcode = PutFullData;
            next_addr   = '0;
            next_wdata  = '0;
            next_state  = IDLE;
          end
        end

        SEND_RREQ: begin
          host_a_valid   = 1'b1;
          host_a.opcode  = next_a_opcode;
          if (host_a_ready & continuous_prefetch_counter == LOAD_AMOUNT - 1) begin
            host_a.address = next_addr + continuous_prefetch_counter * DataWidth / 8;
            next_state = WAIT_RESP;
          end else if (host_a_ready) begin
            host_a.address = next_addr + continuous_prefetch_counter * DataWidth / 8;
            next_state = SEND_RREQ;
          end else begin
            next_state = SEND_RREQ;
          end
        end

        SEND_WREQ: begin
          host_a_valid   = write_en;
          host_a.opcode  = next_a_opcode;
          host_a.size    = WRITE_SIZE;
          if (previous_state == IDLE) begin
            host_a.data    = next_wdata;
          end else begin
            host_a.data    = write_data; // Use the latest write data
          end
          host_a.address = next_addr + continuous_write_counter * DataWidth / 8;
          if (continuous_write_counter == WRITE_AMOUNT - 1 && host_a_ready) begin
            next_state = IDLE;
          end else begin
            next_state = SEND_WREQ;
          end
        end


        WAIT_RESP: begin
          host_a_valid   = 1'b0;
          if ((previous_d_valid == 1'b1 ) & (host_d_valid == 1'b0)) begin
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
endmodule
