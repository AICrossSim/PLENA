#   Recommended usage:
#   bash run_dc.sh
#   
#   Note: Script runs from synopsys/ directory (no separate work_db needed)
#   Note: This script is configured for IP core synthesis (no IO pads)
#
#------------------------------
# Get the Environment Variable
#------------------------------
# Set WORK_DIR to synthesis working directory
set WORK_DIR "./"

#------------------------------
# set the top design
#------------------------------
set top_design "fp_cp_mult"

#------------------------------
# Setup DC logging paths
#------------------------------
set logs_dir ${WORK_DIR}/outputs/logs
# Note: DC internal logging disabled to reduce clutter
# set sh_command_log_file ${logs_dir}/dc_command.log
# set filename_log_file ${logs_dir}/dc_filenames.log

#------------------------------
# set process
#------------------------------
proc cal_freq {clock_period} {
  return [expr 1000/$clock_period];
}

#------------------------------
# set the necessary path
#------------------------------
# Set paths
set src ${WORK_DIR}/../../src
set outputs ${WORK_DIR}/outputs/${top_design}
set run ${WORK_DIR}/outputs/${top_design}/netlist
set log ${WORK_DIR}/outputs/${top_design}logs    
set rpt ${WORK_DIR}/outputs/${top_design}/rpt 
set out ${WORK_DIR}/outputs/${top_design}/out

file mkdir ${log}
file mkdir ${outputs}
file mkdir ${run}
file mkdir ${rpt}
file mkdir ${out}
file mkdir ${logs_dir}

#------------------------------
# Set the limited log messages
#------------------------------
set_message_info -id ELAB-405 -limit 10


#-----------------------------
# Set the source file path
#-----------------------------
lappend search_path  ${src}

# Note: Using default work library (no custom work_db needed)

#---------------------------------------
# Set the clock and reset in the design
#---------------------------------------
set top_clk_name    "clk"
set reset           "rst"
set clk_period      "1000"

#--------------------------
# Read RTL files
#--------------------------
source ${WORK_DIR}/read_rtl.tcl


#-------------------------------------
# Check the design with DW and Gtech
#-------------------------------------
check_design
check_design > ${log}/${top_design}_pre_check.log

#--------------------------
# Set the current design
#--------------------------
current_design ${top_design}

#--------------------------
# link
#--------------------------
link
uniquify

#--------------------------
# timing and area
#--------------------------
# set_max_area 0

#--------------------------
# read user-defined SDC constraint file
#--------------------------
source ${WORK_DIR}/constraints/module_constraints.sdc


#------------------------
# save the flat with DW and gtech
#------------------------
write_file -f verilog -hierarchy -output ${run}/${top_design}_unmapped.v
write_file -f ddc     -hierarchy -output ${run}/${top_design}_unmapped.ddc

#------------------------- 
# compile 
#-------------------------

compile_ultra -retime
# compile


#-------------------------
# change names
#-------------------------
change_names -rules verilog -verbose -hier

#-------------------------
# check
#-------------------------
check_timing > ${log}/${top_design}_uncon_path.log
check_design > ${log}/${top_design}_check.log

#-------------------------
# save the design
#-------------------------


write_file -f verilog -hierarchy -output ${out}/${top_design}_mapped.v
write_file -f ddc     -hierarchy -output ${out}/${top_design}_mapped.ddc
write_sdf ${out}/${top_design}.sdf
write_sdc ${out}/${top_design}.sdc
write_script -format dctcl -hierarchy -output ${run}/${top_design}.tcl

#-------------------------
# report
#-------------------------
report_units > ${rpt}/${top_design}_units.log
report_clock -skew > ${rpt}/${top_design}_clk.log
echo "The frequency of the led is :" >> ${rpt}/${top_design}_clk.log
echo "-----------------------------" >> ${rpt}/${top_design}_clk.log
echo [cal_freq $clk_period] "GHz" >> ${rpt}/${top_design}_clk.log
echo "-----------------------------" >> ${rpt}/${top_design}_clk.log

report_area > ${rpt}/${top_design}_area.log
report_timing > ${rpt}/${top_design}_timing.log
report_timing -delay_type max -max_paths 50 -nworst 1 -significant_digits 3 -sort_by slack > ${rpt}/${top_design}_slack_timing.log
# report_timing -capacitance -transition_time > ${rpt}/${top_design}_timing_cap.log
# report_net -capacitance > ${rpt}/${top_design}_net_cap.log
report_constraints -all_violators > ${rpt}/${top_design}_con.log
report_reference > ${rpt}/${top_design}_reference.log
report_power > ${rpt}/${top_design}_power.log
report_port > ${rpt}/${top_design}_port.log

report_lib typical > ${out}/use_lib.message
report_timing

# Note: Synthesis summary logging removed to reduce clutter
# Statistics available in report files under outputs/reports/

#-------------------------
# exit
#-------------------------
exit

