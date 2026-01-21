# Vivado TCL Script to compile plena.sv
# Usage: vivado -mode batch -source build_plena.tcl

# --------------------------------------------------------------------------------
# 1. Configuration
# --------------------------------------------------------------------------------
# Set the target part. Change this to your specific FPGA part.
# Alveo U280 is selected by default as this is an HBM design.
# set target_part "xcu280-fsvh2892-2L-e"
# Artix-7 XC7A200T (Common package/speed grade used here: fbg676-2. Adjust if needed)
set target_part "xc7a200tfbg676-2"
set output_dir "./build_output"

file mkdir $output_dir

# --------------------------------------------------------------------------------
# 2. Project Setup (Non-Project Mode)
# --------------------------------------------------------------------------------
set_part $target_part

# --------------------------------------------------------------------------------
# 3. Read Sources
# --------------------------------------------------------------------------------
# Explicitly read package files that might be treated as headers
read_verilog -sv ./src/memory/HBM/TileLink_Lib/prim_util_pkg.sv

puts "Reading source files..."
flush stdout

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
puts "Setting top module to 'plena_artix7_wrapper' (wrapper for Artix-7 without external HBM I/O)..."
flush stdout
set_property top plena_artix7_wrapper [current_fileset]

puts "Starting Synthesis..."
flush stdout
# Run synthesis.
# -flatten_hierarchy rebuilt is often good for larger designs.
# Using default options for now.

# Workaround for RAM inference failure: Allow dissolving large memory into registers
set_param synth.elaboration.rodinMoreOptions {rt::set_parameter dissolveMemorySizeLimit 196608}

if { [catch { synth_design -top plena_artix7_wrapper -part $target_part -keep_equivalent_registers -no_timing_driven } err] } {
    puts "Error during synthesis: $err"
    exit 1
}

# Mark all BRAMs with DONT_TOUCH to prevent optimization
puts "Marking BRAMs as DONT_TOUCH to preserve them through optimization..."
flush stdout
set ramb_cells [get_cells -hierarchical -filter {REF_NAME =~ RAMB* || PRIMITIVE_TYPE =~ BMEM.*}]
if {[llength $ramb_cells] > 0} {
    set_property DONT_TOUCH true $ramb_cells
    puts "  Preserved [llength $ramb_cells] BRAM cells"
} else {
    puts "  Warning: No BRAM cells found to preserve"
}

puts "Running opt_design with reduced optimization to preserve BRAMs..."
flush stdout
# Use -directive RuntimeOptimized to reduce aggressive optimization that removes "unused" BRAMs
opt_design -directive RuntimeOptimized

# --------------------------------------------------------------------------------
# 5. Reporting and Checkpoints
# --------------------------------------------------------------------------------
puts "Writing Checkpoint..."
flush stdout
write_checkpoint -force $output_dir/post_synth.dcp

puts "Generating Reports..."
flush stdout
report_utilization -file $output_dir/utilization.rpt
report_utilization -hierarchical -file $output_dir/utilization_hierarchical.rpt
report_timing_summary -file $output_dir/timing_summary.rpt

puts "Done. Results are in $output_dir"
