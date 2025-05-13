#!/bin/bash
python fp_2_mx_fp_block_tb.py
gtkwave ./build/fp_2_mx_fp_block/test_0/dump.vcd fp_2_mxfp_experiment.gtkw