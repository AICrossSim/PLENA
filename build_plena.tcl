# Vivado TCL Script to compile plena.sv
# Usage: vivado -mode batch -source build_plena.tcl

# --------------------------------------------------------------------------------
# 1. Configuration
# --------------------------------------------------------------------------------
# Set the target part. Change this to your specific FPGA part.
# Alveo U280 is selected by default as this is an HBM design.
set target_part "xccu280-fsvh2892-2L-e"
set output_dir "./build_output"

file mkdir $output_dir

# --------------------------------------------------------------------------------
# 2. Project Setup (Non-Project Mode)
# --------------------------------------------------------------------------------
set_part $target_part

# --------------------------------------------------------------------------------
# 3. Read Sources
# --------------------------------------------------------------------------------
puts "Reading source files..."

# Recursively add all files in src/
# This works well for mixed .sv and .v hierarchies
add_files -scan_for_includes ./src

# Explicitly set include directories if automatic scanning misses them
# based on the file locations "src/definitions" seems to be the main one.
set_property include_dirs [list \
    [file normalize "./src/definitions"] \
] [current_fileset]

# --------------------------------------------------------------------------------
# 4. Synthesis
# --------------------------------------------------------------------------------
puts "Setting top module to 'plena'..."
set_property top plena [current_fileset]

puts "Starting Synthesis..."
# Run synthesis.
# -flatten_hierarchy rebuilt is often good for larger designs.
# Using default options for now.
if { [catch { synth_design -top plena -part $target_part } err] } {
    puts "Error during synthesis: $err"
    exit 1
}

# --------------------------------------------------------------------------------
# 5. Reporting and Checkpoints
# --------------------------------------------------------------------------------
puts "Writing Checkpoint..."
write_checkpoint -force $output_dir/post_synth.dcp

puts "Generating Reports..."
report_utilization -file $output_dir/utilization.rpt
report_timing_summary -file $output_dir/timing_summary.rpt

puts "Done. Results are in $output_dir"
