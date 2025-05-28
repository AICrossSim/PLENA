
reset_run synth_1
launch_runs synth_1 -jobs 30
wait_on_run synth_1
open_run synth_1 -name synth_1
report_utilization -file ../synthesis_report/BOOM_utilization_synth.rpt
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 10 -input_pins -routable_nets -name timing_1 -file ../synthesis_report/BOOM_timing_synth.rpt
report_power -file ../synthesis_report/BOOM_power_synth.rpt
close_project