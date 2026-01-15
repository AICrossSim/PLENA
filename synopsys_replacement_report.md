# Synopsys DesignWare IP Replacement Report

## Overview
The PLENA codebase currently uses **6 specific Synopsys DesignWare (DW) floating-point modules**. To synthesize in Vivado, you must replace these with equivalent Xilinx Floating-Point Operator IPs.

The current architecture wraps the combinatorial DW IP with a `register_slice` to provide a `valid`/`ready` handshake interface. This is fortunate, as it allows you to easily substitute Xilinx AXI4-Stream IPs (which inherently use `tvalid`/`tready`) without breaking the pipeline, despite the likely increase in latency.

## Required IP Replacements

You need to create replacements for the following wrapper modules in `src/basic_components/synopsis_ip_inst/rtl/`.

| Synopsys IP | Wrapper File | Recommended Xilinx IP Config |
| :--- | :--- | :--- |
| **DW_fp_add** | `DW_fp_add_inst.sv` | **Floating-point Add/Subtract** <br> • Operation: Add <br> • Flow Control: NonBlocking <br> • Interface: AXI4-Stream |
| **DW_fp_mult** | `DW_fp_mult_inst.sv` | **Floating-point Multiply** <br> • Operation: Multiply <br> • Interface: AXI4-Stream |
| **DW_fp_sqrt** | `DW_fp_sqrt_inst.sv` | **Floating-point Square Root** <br> • Operation: Sqrt <br> • Interface: AXI4-Stream |
| **DW_fp_exp** | `DW_fp_exp_inst.sv` | **Floating-point Exponential** <br> • Operation: Exponential <br> • Interface: AXI4-Stream |
| **DW_fp_exp2** | `DW_fp_exp2_inst.sv` | **Floating-point Exponential** <br> • Operation: Exponential (Base 2 if avail, else Base e * ln2) <br> *Note: Vivado might not have native exp2. May need `Fixed -> Float` logic or custom LUT.* |
| **DW_fp_recip** | `DW_fp_recip_inst.sv` | **Floating-point Reciprocal** <br> • Operation: Reciprocal <br> • Interface: AXI4-Stream |

## Implementation Guide

### 1. The Wrapper Utility
All current wrappers follow this pattern:
```systemverilog
// Current Design
DW_fp_xxx U1 ( .a(in), .z(out_comb) ); // Combinatorial
register_slice reg_inst ( .data_in(out_comb), ... ); // Handshake
```

### 2. The Replacement Pattern
You should modify the `_inst.sv` files to instantiate a Xilinx IP directly, wiring the handshaking signals to the IP's AXI Stream interface.

**Example Replacement for `DW_fp_add_inst.sv`**:
```systemverilog
module DW_fp_add_inst #(
    parameter int EXP_WIDTH = 8,
    parameter int MANT_WIDTH = 23
)(
    input clk,  // IPs need clock
    input rst,  // IPs need aresetn (inverted)
    // ... data signals
);

    // Xilinx IP Instance (generated from IP Catalog)
    // Assumes AXI Stream naming convention
    xilinx_fp_add_ip u_xilinx_add (
        .aclk(clk),
        .aresetn(!rst),
        .s_axis_a_tvalid(data_in_valid),
        .s_axis_a_tready(data_in_ready), // Note: You might need to split ready if 2 inputs
        .s_axis_a_tdata(data_a),
        .s_axis_b_tvalid(data_in_valid), // Sync inputs
        // .s_axis_b_tready(),           // Usually tied with a_ready
        .s_axis_b_tdata(data_b),
        .m_axis_result_tvalid(data_out_valid),
        .m_axis_result_tready(data_out_ready),
        .m_axis_result_tdata(data_out)
    );
endmodule
```

## Potential Issues

### 1. Parameterization
The current modules are parameterized (`EXP_WIDTH`, `MANT_WIDTH`).
*   **Problem**: Xilinx IPs are static (generated for a specific width, e.g., IEEE Single 32-bit).
*   **Solution**: You likely use `BF16` (8 exp, 7 mant) or `FP32` (8 exp, 23 mant). You cannot easily support *dynamic* parameters with Xilinx IP Catalog. You must generate fixed IPs for the specific precisions used in PLENA (likely `BF16` and `FP32`) and conditionalize the instantiation or create explicit variants.

### 2. Latency
*   **DW**: 0 cycles (Combinatorial).
*   **Xilinx**: >0 cycles (Pipelined).
*   **Impact**: Since the system uses `valid`/`ready` handshaking, the extra latency *should* be absorbed by the flow control. However, throughput might change. Ensure the `register_slice` logic in other parts of the system doesn't have implicit latency timeout assumptions.

### 3. Missing `EXP2`
Standard Xilinx FP Operator might not support `2^x` directly (it supports `e^x`).
*   **Workaround**: Pre-multiply input by `ln(2)` then use `e^x`. Or use a look-up table if precision allows.
