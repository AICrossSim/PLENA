create_project Coprocessor_Vivado_Prj /home/hw1020/Coprocessor_for_Llama/Coprocessor_Vivado_Prj -part xcvu37p-fsvh2892-2L-e
set_property board_part xilinx.com:vcu128:part0:1.0 [current_project]
add_files [glob ../../src/*]
set_property top coprocessor [get_filesets sim_1]
add_files -fileset constrs_1 -norecurse ../../tools/vivado/time_constraint.xdc