#!/bin/sh

# cleanup
rm -rf obj_dir
rm -f AXIS_tb.vcd

# run Verliator to translate Verilog into C++, including C++ testbench
verilator -Wall --cc --exe tb_vec_elem_acc.cpp vec_elem_acc.sv --top-module vec_elem_acc
make -C obj_dir -f Vvec_elem_acc.mk Vvec_elem_acc
./obj_dir/Vvec_elem_acc