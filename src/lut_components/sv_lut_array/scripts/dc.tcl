remove_design -all
#################################### set library ########################################
# this is the library path for the TSMC 28nm process, set yout own library path here
set techlib_path    ./lib/asap7
set std_cell_path   ${techlib_path}/asap7sc7p5t_28

set search_path "$search_path \
../rtl \
../scripts \
/home/cx922/Coprocessor_for_Llama/tools/synopsys/lib/asap7/asap7sc7p5t_28/ \
"

set target_library      "asap7sc7p5t_SIMPLE_RVT_TT_ccs_211120.db \
                         asap7sc7p5t_AO_RVT_TT_ccs_211120.db \
                         asap7sc7p5t_SEQ_RVT_TT_ccs_220123.db \
                         asap7sc7p5t_INVBUF_RVT_TT_ccs_211120.db \
                         "

set synthetic_library   "dw_foundation.sldb"
set link_library        " $target_library $synthetic_library"
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#  ASAP7 7nm Library Setup for IP Core Design
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Note: ASAP7 does not include I/O libraries (academic PDK for research)
# This setup is optimized for IP core design (no IO pads required)

#################################### set location #######################################
set top_design fp_lut_array_b_cycle_stage1
# set your name here

# set top_design lut_16

set outdir ..

###################################### initial ##########################################
# analyze -format sverilog  ../rtl/Parameters.sv
analyze -format sverilog  ../rtl/${top_design}.sv

elaborate $top_design
link

################################## add constraint ######################################
source constraint.tcl
source namingrules.tcl

#################################### compile #######################################
#set_flatten true
compile
# compile_ultra -retime -area_high_effort_script

#compile_ultra -timing_high_effort_script

############################ save results ##################################

# write -format verilog -hier -out $outdir/netlists/${top_design}.nl.v
# write_sdf $outdir/reports/${top_design}.sdf
# write_sdc $outdir/reports/${top_design}.sdc
# write -format ddc -hier -o $outdir/netlists/${top_design}.ddc
report_area -hier > $outdir/reports/area_${top_design}.rpt
report_power > $outdir/reports/power_${top_design}.rpt
report_constraint -all_violators > $outdir/reports/violation_${top_design}.rpt
report_timing -delay max > $outdir/reports/timing_${top_design}.rpt
report_timing -delay min >> $outdir/reports/timing_${top_design}.rpt

#check_design

#write -format verilog -hier -out $outdir/netlists/${top_design}.v
##write_sdf $outdir/reports/${top_design}.sdf
##write_sdc $outdir/reports/${top_design}.sdc
##report_area -hier > $outdir/reports/area.rpt
##report_power > $outdir/reports/power.rpt
##report_constraint -all_violators > $outdir/reports/violation.rpt
##report_timing -delay max > $outdir/reports/timing.rpt
##report_timing -delay min >> $outdir/reports/timing.rpt
#
######################################## quit ##########################################
#
