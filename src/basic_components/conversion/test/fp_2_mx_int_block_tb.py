#!/usr/bin/env python3

import logging
import torch
import math

import cocotb
from cocotb.log import SimLog

from cfl_cocotb.testbench import CombinationalTestbench
from cfl_cocotb.runner import veri_runner, SRC_PATH
from cfl_cocotb.torch_fp_conversion import pack_fp_to_bin

from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware
from quant.quantizer.hardware_quantizer.mxint import _mx_int_quantize_hardware
from cfl_tools.debugger import set_excepthook, get_dut_attributes

logger = logging.getLogger("testbench")
logger.setLevel(logging.DEBUG)

torch.manual_seed(42)


class FP2MXIntBlockTB(CombinationalTestbench):
    def generate_inputs(self, num):
        self.q_config = {
            "BLOCK_DIM": self.dut.BLOCK_DIM.value,
            "FP_MANT_WIDTH": self.dut.FP_MANT_WIDTH.value,
            "FP_EXP_WIDTH": self.dut.FP_EXP_WIDTH.value,
            "MXINT_MANT_WIDTH": self.dut.MXINT_MANT_WIDTH.value,
            "MXINT_SCALE_WIDTH": self.dut.MXINT_SCALE_WIDTH.value,
        }

        BLOCK_DIM = self.q_config["BLOCK_DIM"]
        FP_WIDTH = self.q_config["FP_EXP_WIDTH"] + self.q_config["FP_MANT_WIDTH"] + 1
        
        # Generate random FP numbers
        x = torch.randn(num, BLOCK_DIM) * self.range
        
        # Lists to hold inputs and outputs
        data_in_list = []
        element_data_out_list = []
        scale_data_out_list = []
        
        # Process each block
        for block_idx in range(num):
            block_data = x[block_idx]
            
            # Quantize to minifloat
            qx, x_exp, x_mant = _minifloat_ieee_quantize_hardware(
                block_data, FP_WIDTH, self.q_config["FP_EXP_WIDTH"]
            )
            
            # Convert to MXINT using the existing hardware quantizer
            out_x, out_mant, out_scale = _mx_int_quantize_hardware(
                qx.unsqueeze(0),  # Shape: [1, BLOCK_DIM]
                self.q_config["MXINT_MANT_WIDTH"],
                self.q_config["MXINT_SCALE_WIDTH"],
                None,
                [1, BLOCK_DIM],
            )
            
            # Pack FP numbers for input to RTL
            fp_packed = pack_fp_to_bin(
                x_exp, x_mant, 
                self.q_config["FP_EXP_WIDTH"], 
                self.q_config["FP_MANT_WIDTH"]
            )

            data_in_list.append(fp_packed.tolist())
            
            # Extract expected outputs
            block_scale = int(out_scale.flatten()[0].item())
            scale_data_out_list.append(block_scale)
            
            # Get mantissa values and convert to integer representation
            expected_mants = (out_mant * 2**(self.q_config["MXINT_MANT_WIDTH"] - 1)).int().flatten().tolist()[:BLOCK_DIM]
            element_data_out_list.append(expected_mants)
            
            # Debug logging
            self.log.debug(f"Block {block_idx}:")
            self.log.debug(f"  Input FP values: {block_data.tolist()}")
            self.log.debug(f"  Quantized exps: {x_exp.tolist()}")
            self.log.debug(f"  Quantized mants: {x_mant.tolist()}")
            self.log.debug(f"  Expected MXINT scale: {block_scale}")
            self.log.debug(f"  Expected MXINT mants: {expected_mants}")
        
        # Store inputs and outputs in the format expected by CombinationalTestbench
        self.inputs = {
            "data_in": data_in_list,
        }
        self.outputs = {
            "element_data_out": element_data_out_list,
            "scale_data_out": scale_data_out_list,
        }
    

    def check_output(self, input, output):
        self.log.debug(f"Expected result : {input}, got: {output}")
        self.log.debug(f"----------------{self.dut}---------")
        # get_dut_attributes(self.dut, self.log, None)
        # self.log.debug(f"----------------{self.dut.fp_ieee_exponent_casting_inst}---------")
        # get_dut_attributes(self.dut.fp_ieee_exponent_casting_inst, self.log, None)
        # self.log.debug(f"----------------{self.dut.fp_ieee_mantissa_casting_inst}---------")
        # get_dut_attributes(self.dut.fp_ieee_mantissa_casting_inst, self.log, None)

        if isinstance(output, list):
            for i in range(len(input)):
                assert input[i] == output[i], f"Expected element {self.output_name} {input[i]}, but got {output[i].signed_integer}"
        else:
            assert input == output, f"Expected element {self.output_name} {input}, but got {output.signed_integer}"



@cocotb.test()
async def test(dut):
    tb = FP2MXIntBlockTB(dut)
    tb.log.setLevel(logging.DEBUG)
    tb.range = 10.0
    await tb.run_test(num=100)


if __name__ == "__main__":
    veri_runner(
        trace=True,
        module="fp_2_mx_int_block",
        group="conversion",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/fp_operation"),
            str(SRC_PATH / "basic_components/cast"),
        ],
        module_param_list=[
            {
                "BLOCK_DIM": 8,
                "FP_MANT_WIDTH": 3,
                "FP_EXP_WIDTH": 4
            }
        ]
    )
