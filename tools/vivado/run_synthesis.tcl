open_project Coprocessor_Vivado_Prj.xpr
remove_files [get_files *]
add_files [glob ../src/*]
set_property top coprocessor [get_filesets sim_1]
add_files -fileset constrs_1 -norecurse ../tools/vivado/time_constraint.xdc

reset_run synth_1
launch_runs synth_1 -jobs 40
wait_on_run synth_1
open_run synth_1 -name synth_1
report_utilization -file ./tools/synthesis_report/RC_Utilisation.rpt
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 10 -input_pins -routable_nets -name timing_1 -file ./tools/synthesis_report/RC_timing_synth.rpt
close_project