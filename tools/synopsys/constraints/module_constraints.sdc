# top_clk, top_clk_name, reset, clk_period
# Note: New coprocessor module has instruction interface and TileLink HBM ports

# SDC Constraints for Coprocessor IP Module
# Note: This is an internal IP, not connected to chip pads

#---------------------------------------
# Create Clock
#---------------------------------------
# Primary system clock - use explicit clock name
create_clock -period $clk_period [get_ports clk] -name clk
set_dont_touch_network [get_clocks clk]

# Clock uncertainty (jitter + skew)
set_clock_uncertainty -setup [expr $clk_period * 0.05] [get_clocks clk]
set_clock_uncertainty -hold  [expr $clk_period * 0.02] [get_clocks clk]

#---------------------------------------
# Reset Constraints
#---------------------------------------
# Asynchronous reset, synchronous deassertion
set_false_path -from [get_ports rst]

#---------------------------------------
# Input/Output Timing Constraints
#---------------------------------------
# For internal IP, assume reasonable input/output delays relative to the system clock

# Instruction Interface Timing
puts "--------- clk period ---------"
puts $clk_period

set_input_delay  [expr $clk_period * 0.1] -clock clk [get_ports data_a]
set_input_delay  [expr $clk_period * 0.1] -clock clk [get_ports data_b]
set_input_delay  [expr $clk_period * 0.1] -clock clk [get_ports data_in_valid]
set_input_delay  [expr $clk_period * 0.1] -clock clk [get_ports data_out_ready]
set_output_delay [expr $clk_period * 0.1] -clock clk -add_delay [get_ports data_out]
set_output_delay [expr $clk_period * 0.1] -clock clk -add_delay [get_ports data_out_valid]


#---------------------------------------
# Internal IP Specific Constraints
#---------------------------------------
# Set a reasonable load and drive for internal connections
set_load 0.005 [all_outputs]

#---------------------------------------
# Maximum Transition and Capacitance
#---------------------------------------
# Conservative limits for internal IP
set_max_transition 0.5 [current_design]
set_max_capacitance 0.1 [current_design]

