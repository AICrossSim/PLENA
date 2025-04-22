#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os

from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

from cfl_cocotb import veri_runner, packed_array_analyser, MXBlockFPConverter

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

# Parameters Definition
# ---------------------

mxfp_exp_width = 4
mxfp_mant_width = 3
mxfp_scale_width = 8
block_dim = 2

SRAM_DEPTH = 128
MLEN = 4
Parallel_Wr_Dim = 2
Parallel_Rd_Dim = 2

generator = MXBlockFPConverter(mxfp_exp_width, mxfp_mant_width, mxfp_scale_width, block_dim)

@cocotb.test()
async def sram_function_test(dut):
    """Basic Cocotb test for my design."""
    
    element_array_analyser = packed_array_analyser  (mxfp_exp_width + mxfp_mant_width + 1, MLEN, Parallel_Wr_Dim, Parallel_Rd_Dim)
    scale_array_analyser = packed_array_analyser    (mxfp_scale_width, MLEN, Parallel_Wr_Dim, Parallel_Rd_Dim)

    # Start clock generation
    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())  # 2ns period (1GHz clock)
    await Timer(5, units="ns")
    
    cocotb.log.info("Starting SRAM test")
    dut.rst.value = 0
    await Timer(5, units="ns")  # Hold reset for 5ns
    dut.rst.value = 1
    await Timer(5, units="ns")  # Allow some settling time




    # Write to sram
    for i in range(MLEN // Parallel_Wr_Dim):
        dut.req.value = 1
        dut.write_en.value = 1
        dut.sram_addr.value = (Parallel_Wr_Dim // Parallel_Rd_Dim) * i

        m_mx_fp_scales, m_mx_fp_elems = generator.generate_certain_values([1.24, 2.01, 1.0231, 0.9820, 3.14, 0.91, 2.4131, 0.4820])
        m_ele_data = 0
        m_scale_data = 0

        for i in range(MLEN * Parallel_Wr_Dim // block_dim):
            m_ele_data    += sum((m_mx_fp_elems[i][n] << (mxfp_exp_width + mxfp_mant_width + 1) * (n + i * block_dim) ) for n in range(block_dim))
            m_scale_data  += (m_mx_fp_scales[i] << (mxfp_scale_width) * i)        
        dut.element_in.value = m_ele_data
        dut.scale_in.value = m_scale_data
        
        # raise Exception("Stop")
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        cocotb.log.info("Write Content SRAM test at Addr: %d", dut.sram_addr.value)
        element_array_analyser.print_wdata_from_hbm(f"{dut.element_in.value}")
        scale_array_analyser.print_wdata_from_hbm(f"{dut.scale_in.value}")
        # cocotb.log.info(f"ELEMENT HBM")
        # element_array_analyser.print_wdata_from_hbm(f"{dut.element_in.value}")
        # cocotb.log.info(f"SCALE HBM")
        # scale_array_analyser.print_wdata_from_hbm(f"{dut.scale_in.value}")
        # cocotb.log.info(f"Write Addr: {dut.sram_addr.value}")
        # cocotb.log.info(f"ELEMENT SRAM")
        # element_array_analyser.print_wdata_from_hbm(f"{dut.element_storage.sub_sram_wdata.value}")
        # element_array_analyser.print_write_data_to_sram(f"{dut.element_storage.sub_sram_wdata.value}", [0])
        # cocotb.log.info(f"SCALE SRAM")
        # scale_array_analyser.print_wdata_from_hbm(f"{dut.scale_storage.sub_sram_wdata.value}")
        # scale_array_analyser.print_write_data_to_sram(f"{dut.scale_storage.sub_sram_wdata.value}", [0])
    
    # Read from sram

    dut.req.value = 1
    dut.write_en.value = 0
    dut.sram_addr.value = 0
    dut.transposed_read.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    cocotb.log.info("<----------------Row Read at Addr: %d --------------->", dut.sram_addr.value)
    cocotb.log.info(f"Loaded OUT HBM")
    element_array_analyser.print_rdata_from_overall_sram(f"{dut.element_out.value}")
    cocotb.log.info(f"SCALE OUT HBM")
    scale_array_analyser.print_rdata_from_overall_sram(f"{dut.scale_out.value}")
    

    # Transposed Read from sram
    dut.req.value = 1
    dut.write_en.value = 0
    dut.sram_addr.value = 0
    dut.transposed_read.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    cocotb.log.info("<----------------Col Read at Addr: %d --------------->", dut.sram_addr.value)
    cocotb.log.info(f"Loaded OUT HBM")
    element_array_analyser.print_rdata_from_overall_sram(f"{dut.loaded_element_out.value}")
    cocotb.log.info(f"LOADED SCALE OUTPUT")
    scale_array_analyser.print_rdata_from_overall_sram(f"{dut.loaded_scale_out.value}")


    # Keep simulation running to observe clock
    await Timer(10, units="ns")

@pytest.mark.dev
def test_simple_mvsram():
    # Run tests with different params
    veri_runner(
        group = "matrix_sram",
        module = "matrix_sram_with_rounding",
        additional_include_paths = [
            "../../../../src/basic_components/mx_fp_operation",
            "../../../../src/basic_components/common"
        ],  
        module_param_list=[
            {"MXFP_EXP_WIDTH": mxfp_exp_width, "MXFP_MANT_WIDTH": mxfp_mant_width, "MXFP_SCALE_WIDTH": mxfp_scale_width, "BLOCK_DIM": block_dim, "SRAM_DEPTH": SRAM_DEPTH, "MLEN": MLEN, "PARALLEL_DIM" : Parallel_Wr_Dim},
        ],
        trace = True,
    )


if __name__ == "__main__":
    test_simple_mvsram()
