#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os

from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

import torch

from cfl_cocotb import veri_runner
from cfl_cocotb.runner import SRC_PATH
from cfl_cocotb.testbench import Testbench
from cfl_cocotb.fp_generation import TorchFpGenerator
from cfl_cocotb.streaming import StreamMonitor, MultiSignalStreamDriver

from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware
from cfl_cocotb.torch_fp_conversion import pack_fp_to_bin
from cfl_tools.debugger import set_excepthook, get_dut_attributes
from cocotb.log import SimLog


class FPVectorReduceLayerTB(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut, dut.clk, dut.rst)

        if not hasattr(self, "log"):
            self.log = SimLog("%s" % (type(self).__qualname__))
            self.log.setLevel(logging.DEBUG)

        # * Drivers
        self.in_driver = MultiSignalStreamDriver(
            dut.clk, (dut.data_in,), dut.data_in_valid, dut.data_in_ready
        )

        self.out_monitor = StreamMonitor(
            dut.clk,
            dut.data_out,
            dut.data_out_valid,
            dut.data_out_ready,
            check=True,
            unsigned=True,
        )

    def generate_inputs(self, num):
        q_config = {
            "LAYER_DIM" : self.dut.LAYER_DIM.value,
            "IN_MAN_WIDTH" : self.dut.IN_MAN_WIDTH.value,
            "IN_EXP_WIDTH" : self.dut.IN_EXP_WIDTH.value,
            "EXT_MANT_WIDTH" : self.dut.EXT_MANT_WIDTH.value,
            "EXT_EXP_WIDTH" : self.dut.EXT_EXP_WIDTH.value,
        }
        
        layer_dim = q_config["LAYER_DIM"]
        in_width = q_config["IN_MAN_WIDTH"] + q_config["IN_EXP_WIDTH"] + 1
        out_width = in_width + q_config["EXT_MANT_WIDTH"] + q_config["EXT_EXP_WIDTH"]

        torch.manual_seed(0)
        torch_data = torch.randn(num, layer_dim)

        # Quantize inputs
        qa, a_exp, a_mant = _minifloat_ieee_quantize_hardware(torch_data, in_width, q_config["IN_EXP_WIDTH"])
        inputs_bin = pack_fp_to_bin(a_exp, a_mant, q_config["IN_EXP_WIDTH"], q_config["IN_MAN_WIDTH"])
        
        # Calculate expected outputs (MAX reduction)
        # Assuming LAYER_DIM is even and we reduce in pairs
        out_f = torch.stack([torch.max(qa[:, 2*i], qa[:, 2*i+1]) for i in range(layer_dim // 2)], dim=1)
        
        # Quantize and pack outputs
        qout, out_exp, out_mant = _minifloat_ieee_quantize_hardware(out_f, out_width, q_config["IN_EXP_WIDTH"] + q_config["EXT_EXP_WIDTH"])
        outputs_bin = pack_fp_to_bin(out_exp, out_mant, q_config["IN_EXP_WIDTH"] + q_config["EXT_EXP_WIDTH"], q_config["IN_MAN_WIDTH"] + q_config["EXT_MANT_WIDTH"])

        self.inputs = []
        for i in range(num):
            packed_in = 0
            for j in range(layer_dim):
                packed_in |= (int(inputs_bin[i, j]) << (j * in_width))
            self.inputs.append((packed_in,))

        self.outputs = []
        for i in range(num):
            packed_out = 0
            for j in range(layer_dim // 2):
                packed_out |= (int(outputs_bin[i, j]) << (j * out_width))
            self.outputs.append(packed_out)

    async def run_test(self, us, num):
        await self.reset()
        self.log.info(f"Reset finished")
        
        # Set operation to MAX (2)
        self.dut.operation.value = 2
        
        self.out_monitor.ready.value = 1

        self.generate_inputs(num)   

        self.in_driver.load_driver(self.inputs)
        self.out_monitor.load_monitor(self.outputs)

        await Timer(100, units="ns")
        await Timer(us, units="us")
        assert self.out_monitor.exp_queue.empty()

@cocotb.test()
async def test(dut):
    tb = FPVectorReduceLayerTB(dut)
    tb.log.setLevel(logging.DEBUG)
    await tb.run_test(10, 10)


@pytest.mark.dev
def test_fp_vector_max_reduction():
    layer_dim = 4
    in_exp = 4
    in_man = 3
    in_width = in_exp + in_man + 1
    
    veri_runner(
        group = "vector_machine",
        module = "fp_vector_reduce_layer",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/buffer"),
            str(SRC_PATH / "basic_components/fp_operation"),
            str(SRC_PATH / "basic_components/int_operation")
        ],
        definitions_path = str(SRC_PATH / "definitions"),
        module_param_list=[
            {
                "OVERALL_INPUT_WIDTH": layer_dim * in_width,
                "LAYER_DIM": layer_dim,
                "IN_MAN_WIDTH": in_man,
                "IN_EXP_WIDTH": in_exp,
                "EXT_MANT_WIDTH": 0,
                "EXT_EXP_WIDTH": 0
            },
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_fp_vector_max_reduction()
