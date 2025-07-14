#!/bin/sh

# cleanup
rm -rf obj_dir
rm -f AXIS_tb.vcd

# run Verliator to translate Verilog into C++, including C++ testbench
verilator -Wall --cc --exe tb_vec_shift.cpp vec_shift.sv --top-module vec_shift
make -C obj_dir -f Vvec_shift.mk Vvec_shift
./obj_dir/Vvec_shift