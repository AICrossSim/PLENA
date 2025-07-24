#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os

from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
import math
import torch
from pathlib import Path
import numpy as np
from cfl_cocotb import veri_runner
from cfl_cocotb.runner import SRC_PATH
from cfl_cocotb.testbench import Testbench
from cfl_cocotb.fp_generation import TorchFpGenerator
from cfl_cocotb.streaming import StreamMonitor, MultiSignalStreamDriver

from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware
from cfl_cocotb.torch_fp_conversion import pack_fp_to_bin
from cfl_tools.debugger import set_excepthook, get_dut_attributes
from cocotb.log import SimLog

# Import the golden model functions
from test_prefix_scan import hw_prefix_scan as golden_hw_prefix_scan
from test_prefix_scan import fp_to_float

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

@cocotb.test()
async def simple_prefix_scan_test(dut):
    # Get configuration from DUT
    q_config = {
        "IN_EXP_WIDTH": dut.IN_EXP_WIDTH.value,
        "IN_FIX_WIDTH": dut.IN_FIX_WIDTH.value, 
        "IN_FIX_FRAC_WIDTH": dut.IN_FIX_FRAC_WIDTH.value,
        "OUT_EXP_WIDTH": dut.OUT_EXP_WIDTH.value,
        "OUT_FIX_WIDTH": dut.OUT_FIX_WIDTH.value,
        "OUT_FIX_FRAC_WIDTH": dut.OUT_FIX_FRAC_WIDTH.value,
        "N": dut.N.value,
    }
    
    # Start clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    N = q_config["N"]
    
    # Use exactly the same inputs as the golden model
    exp_in = np.array([0, 1, 0, -1, 0, 1, 2, 2])  # Smaller exponents
    # exp_in = np.array([1, 1, 1, 1, 1, 1, 1, 1])  # Smaller exponents
    mant_in = np.array([2, 2, 1, 1, 1, 1, 2, 1])      # Smaller mantissas
    
    # Create tensor from values just like golden model
    fp_in = torch.tensor([mant_in[i] * 2.0**exp_in[i] for i in range(len(exp_in))], dtype=torch.float32)
    result = torch.cumsum(fp_in, dim=0)
    
    # Calculate expected output using golden model
    golden_exp, golden_mant = golden_hw_prefix_scan(
        exp_in.tolist(), mant_in.tolist(),
        q_config["IN_EXP_WIDTH"], q_config["IN_FIX_WIDTH"], q_config["IN_FIX_FRAC_WIDTH"],
        q_config["OUT_EXP_WIDTH"], q_config["OUT_FIX_WIDTH"], q_config["OUT_FIX_FRAC_WIDTH"]
    )
    
    # Calculate frac_diff just like golden model
    frac_diff = q_config["OUT_FIX_FRAC_WIDTH"] - q_config["IN_FIX_FRAC_WIDTH"]
    
    # Reset DUT
    dut.rst.value = 1
    for _ in range(5):
        await RisingEdge(dut.clk)
    
    # Apply inputs exactly as in the golden model
    dut.rst.value = 0
    dut.in_ready.value = 1
    
    # Pack inputs using the same exp_in and mant_in as golden model
    exp_in_packed = 0
    mant_in_packed = 0
    for i in range(N):
        exp_in_packed |= (int(exp_in[i]) & ((1 << q_config["IN_EXP_WIDTH"]) - 1)) << (i * q_config["IN_EXP_WIDTH"])
        mant_in_packed |= (int(mant_in[i]) & ((1 << q_config["IN_FIX_WIDTH"]) - 1)) << (i * q_config["IN_FIX_WIDTH"])
    
    # Debug prints for packing
    print(f"Input exponents: {exp_in.tolist()}")
    print(f"Input mantissas: {mant_in.tolist()}")
    print(f"Packed exp_in: {bin(exp_in_packed)}, width: {exp_in_packed.bit_length()}")
    print(f"Packed mant_in: {bin(mant_in_packed)}, width: {mant_in_packed.bit_length()}")

    # Drive the DUT
    dut.exp_in.value = exp_in_packed
    dut.mant_in.value = mant_in_packed
    
    await RisingEdge(dut.clk)
    dut.in_ready.value = 0
    
    # Wait for output ready
    while not dut.out_ready.value:
        await RisingEdge(dut.clk)
    
    # Capture outputs
    exp_out_packed = dut.exp_out.value
    mant_out_packed = dut.mant_out.value
    
    # Unpack results with debug printing
    actual_exp = []
    actual_mant = []
    for i in range(N):
        exp_mask = (1 << q_config["OUT_EXP_WIDTH"]) - 1
        mant_mask = (1 << q_config["OUT_FIX_WIDTH"]) - 1
        
        # Calculate bit positions for each value
        exp_shift = i * q_config["OUT_EXP_WIDTH"]
        mant_shift = i * q_config["OUT_FIX_WIDTH"]
        
        # Extract values with proper masking
        e = (exp_out_packed >> exp_shift) & exp_mask
        m = (mant_out_packed >> mant_shift) & mant_mask
        
        # Debug prints to verify bit widths
        print(f"Index {i} mantissa raw bits: {bin(m)}, width: {m.bit_length()}")
        
        # Handle sign extension properly for signed values
        if e & (1 << (q_config["OUT_EXP_WIDTH"] - 1)):
            e = e | (~0 << q_config["OUT_EXP_WIDTH"])  # Better sign extension
        if m & (1 << (q_config["OUT_FIX_WIDTH"] - 1)):
            m = m | (~0 << q_config["OUT_FIX_WIDTH"])  # Better sign extension
        
        actual_exp.append(e)
        actual_mant.append(m)
        
        # Print post-sign-extension values
        print(f"Index {i} final mantissa: {m}, as bits: {bin(m & ((1 << 32) - 1))}")
    
    # Convert hardware results to float using SAME method as golden model
    hw_float_values = fp_to_float(actual_exp, actual_mant, frac_diff, q_config)
    # hw_float_values = fp_to_float(actual_exp, actual_mant, 0, q_config)
    
    # Compare with golden model outputs
    golden_float_values = fp_to_float(golden_exp, golden_mant, frac_diff, q_config)
    
    # Print detailed debug info
    print("Golden model exp:", golden_exp)
    print("Golden model mant:", golden_mant)
    print("Hardware model exp:", actual_exp)
    print("Hardware model mant:", actual_mant)
    print("Expected float values:", result.tolist())
    print("Golden model float values:", golden_float_values)
    print("Hardware float values:", hw_float_values)
    
    # Compare with tolerance instead of exact equality
    def compare_with_tolerance(actual, expected, tol=1e-4):
        return all(abs(a - e) / (abs(e) + 1e-10) < tol for a, e in zip(actual, expected))
    
    # Check both golden model vs expected and hardware vs golden
    assert compare_with_tolerance(golden_float_values, result.tolist()), \
        f"Golden model mismatch with expected: {golden_float_values} vs {result.tolist()}"
    
    assert compare_with_tolerance(hw_float_values, golden_float_values), \
        f"Hardware mismatch with golden model: {hw_float_values} vs {golden_float_values}"
    
    # Also compare mantissas and exponents directly
    for i in range(N):
        print(f"Index {i}:")
        print(f"  Golden exp: {golden_exp[i]}, Hardware exp: {actual_exp[i]}")
        print(f"  Golden mant: {golden_mant[i]}, Hardware mant: {actual_mant[i]}")
        if golden_exp[i] != actual_exp[i] or golden_mant[i] != actual_mant[i]:
            print(f"  *** MISMATCH ***")
            # Check bit patterns
            print(f"  Golden exp bits: {bin(golden_exp[i])}, Hardware exp bits: {bin(actual_exp[i])}")
            print(f"  Golden mant bits: {bin(golden_mant[i])}, Hardware mant bits: {bin(actual_mant[i])}")

    # After capturing outputs
    print(f"Raw exp_out_packed: {bin(exp_out_packed)}")
    print(f"Raw mant_out_packed: {bin(mant_out_packed)}")

@pytest.mark.dev
def test_simple_fp_prefix_scan():
    # Run tests with different params
    veri_runner(
        module = "fp_prefix_scan",  
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/buffer"),
            str(SRC_PATH / "basic_components/fp_operation"),
            str(SRC_PATH / "basic_components/int_operation")
        ],   
        module_param_list=[
            {
                "N": 8, 
                "IN_EXP_WIDTH": 4,
                "IN_FIX_WIDTH": 5,
                "IN_FIX_FRAC_WIDTH": 4,
                "OUT_EXP_WIDTH": 5,
                "OUT_FIX_WIDTH": 12,
                "OUT_FIX_FRAC_WIDTH": 10
            },
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_fp_prefix_scan()

# In fp_prefix_scan.sv, add this for debugging


