#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "tools"))

import logging
import pytest
import cocotb
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
#from test_prefix_scan import hw_prefix_scan as golden_hw_prefix_scan
#from test_prefix_scan import fp_to_float

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

@cocotb.test()
async def simple_prefix_scan_test(dut):
    # Get configuration from DUT
    q_config = {
        "EXP_WIDTH": dut.EXP_WIDTH.value,
        "MANT_WIDTH": dut.MANT_WIDTH.value,
        "N": dut.N.value,
    }
    
    # Start clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    N = q_config["N"]
    width = q_config["MANT_WIDTH"] + q_config["EXP_WIDTH"] + 1 #+1 for sign bit
    # Use exactly the same inputs as the golden model
    # exp_in = np.array([2, 1, 0, 1, 0, 1, 2, 2])  # Smaller exponents
    exp_in = np.array([2, 1, 0, 1])  # Smaller exponents

    # exp_in = np.array([1, 1, 1, 1, 1, 1, 1, 1])  # Smaller exponents
    # mant_in = np.array([2, 2, 1, 1, 1, 1, 2, 1])      # Smaller mantissas
    mant_in = np.array([2, 2, 1, 1])      # Smaller mantissas
    torch.manual_seed(0)
    torch_a = torch.randn(N)
    print(torch_a)
    qa, a_exp, a_mant = _minifloat_ieee_quantize_hardware(torch_a, width, q_config["EXP_WIDTH"])
    inputs_a = pack_fp_to_bin(a_exp, a_mant, q_config["EXP_WIDTH"], q_config["MANT_WIDTH"])
    print(f"Inputs A: {inputs_a}")
    # Create tensor from values just like golden model
    fp_in = torch.tensor([mant_in[i] * 2.0**exp_in[i] for i in range(len(exp_in))], dtype=torch.float32)
    out = torch.cumsum(torch_a, dim=0)
    
    # Reset DUT
    dut.rst.value = 1
    for _ in range(5):
        await RisingEdge(dut.clk)
    
    # Apply inputs exactly as in the golden model
    dut.rst.value = 0
    dut.in_ready.value = 1
    
    # Pack inputs using the same exp_in and mant_in as golden model
    v_packed = 0
    vtest = []
    mant_in_packed = 0
    for i, value in enumerate(inputs_a):
        v_packed |= (value << (i * width))
    # Debug prints for packing
    print(f"Packed input: {bin(v_packed)}")
    # print(f"Full packed input (256 bits): {v_packed:0256b}")  # Format the integer directly
    dut.vin.value = int(v_packed)
    # Option 1: String concatenation approach
    binary_str = ""
    for i in range(N-1, -1, -1):  # Element 0 will be in the LSBs (right side)
        binary_str += format(inputs_a[i], f'0{width}b')  # Zero-pad each value to width bits
    v_packed = int(binary_str, 2)  # Convert completed string to integer

    # Debug print
    print(f"Binary string representation: {binary_str}")
    print(f"Final v_packed: {v_packed:0{N*width}b}")

    # Drive the DUT
    dut.vin.value = v_packed
    
    await RisingEdge(dut.clk)
    dut.in_ready.value = 0
    
    # Wait for output ready
    while not dut.out_ready.value:
        await RisingEdge(dut.clk)
    
    # Capture outputs
    vout_packed = dut.vout.value
    qout, out_exp, out_mant = _minifloat_ieee_quantize_hardware(out, width, q_config["EXP_WIDTH"])
    outputs_out = pack_fp_to_bin(
        out_exp, out_mant,
        q_config["EXP_WIDTH"],
        q_config["MANT_WIDTH"])
    print(f"Output: {outputs_out}" )
    # Unpack results with debug printing
    actual=[]
    for i in range(N):
        value = int(vout_packed >> (i * width)) & ((1 << width) - 1)
        actual.append(value)
    print(f"Unpacked output values: {actual}")
    # Convert hardware results to float using SAME method as golden model
    #hw_float_values = fp_to_float(actual_exp, actual_mant, 0, q_config)
    # hw_float_values = fp_to_float(actual_exp, actual_mant, 0, q_config)
    
    # Compare with golden model outputs
    # golden_float_values = fp_to_float(golden_exp, golden_mant, frac_diff, q_config)
    
    # Print detailed debug info
    # print("Golden model exp:", golden_exp)
    # print("Golden model mant:", golden_mant)
    # print("Hardware model exp:", actual_exp)
    # print("Hardware model mant:", actual_mant)
    # print("Expected float values:", out.tolist())
    # # print("Golden model float values:", golden_float_values)
    # print("Hardware float values:", hw_float_values)

@pytest.mark.dev
def test_simple_fp_prefix_scan():
    # Run tests with different params
    veri_runner(
        module = "fp_prefix_scan_syn",  
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/buffer"),
            str(SRC_PATH / "basic_components/fp_operation"),
            str(SRC_PATH / "basic_components/int_operation"),
            str(SRC_PATH / "basic_components/synopsis_ip_inst"),
            str(SRC_PATH / "basic_components/synopsis")


        ],   
        module_param_list=[
            {
                "N": 8, 
                "EXP_WIDTH": 5,
                "MANT_WIDTH": 5,
            },
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_fp_prefix_scan()

# In fp_prefix_scan.sv, add this for debugging


