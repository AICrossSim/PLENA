create_project Coprocessor_Vivado_Prj /home/hw1020/Coprocessor_for_Llama/Coprocessor_Vivado_Prj -part xcu280-fsvh2892-2L-e
add_files [glob ./src/*]
set_property top coprocessor [current_fileset]
set_property is_enabled false [get_files  ./src/system/rtl/SimTop.sv]
add_files -fileset constrs_1 -norecurse ./tools/vivado/time_constraint.xdc