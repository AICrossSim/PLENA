# Define system clock period
set clk_period 666
set clk_name clk
create_clock -period $clk_period clk
set_drive 0 clk
set_clock_uncertainty -setup [expr 0.1*$clk_period] $clk_name
# set_operating_conditions WCCOM
set auto_wire_load_selection true

# Define design environment
set ALL_INS_EX_CLK [remove_from_collection [all_inputs] [get_ports clk]]
# set_driving_cell -lib_cell -pin Q $ALL_INS_EX_CLK
# set_drive 0 {clk}

# set_load $max_cap [all_outputs]

# Define design constraints

#set_input_delay $clk_q_plus_inv -clock $clk_name [all_inputs]
set_input_delay 0.08 -clock $clk_name [all_inputs]
set_output_delay 0.05 -clock $clk_name [all_outputs]

set max_delay $clk_period

# set_false_path -from [get_points data_reg_reg_0__0_/CLK] -to [get_points data_reg_reg_0__0_/QN]
# set_false_path -from [get_ports in_reg] -to [get_pins data_in[0]]

set_max_delay $max_delay -to [all_outputs]
set_max_delay $max_delay -to [all_registers -data_pins]

