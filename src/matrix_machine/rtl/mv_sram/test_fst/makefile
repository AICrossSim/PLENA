# Set simulator
SIM=verilator
TOPLEVEL_LANG=verilog
VERILOG_SOURCES=$(PWD)/simple_counter.sv
TOPLEVEL=simple_counter
MODULE=test_simple_counter

# Enable waveform tracing and Verilator-specific options
COMPILE_ARGS += --trace --trace-structs --trace-fst -DVM_TRACE_FST --timing
export WAVES=1

# Use Cocotb's Makefile system
include $(shell cocotb-config --makefiles)/Makefile.sim
