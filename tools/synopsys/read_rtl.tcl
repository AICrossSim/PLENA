puts "=========================================="
puts "RTL Debug Script Started"
puts "=========================================="


#------------------------------
# Import package files
#------------------------------
puts "\n=== Import Package Files ==="

# Package files to import
set package_files [list \
    "${src}/definitions/global_define.vh" \
    "${src}/definitions/precision.svh" \
    "${src}/definitions/configuration.svh" \
    "${src}/definitions/operation.svh" \
]

foreach pkg_file $package_files {
    set filename [file tail $pkg_file]
    puts "Importing package: $filename"
    analyze -f sverilog -lib work $pkg_file
}

#------------------------------
# Analyze all .sv files
#------------------------------
puts "\n=== Analyze RTL Files ==="

# Define directories to search
set dir_list [list \
    "definitions" \
    "basic_components/mx_fp_operation/rtl" \
    "basic_components/int_operation/rtl" \
    "basic_components/fp_operation/rtl" \
    "basic_components/fixed_operation/rtl" \
    "basic_components/conversion/rtl" \
    "basic_components/common/rtl" \
    "basic_components/cast/rtl" \
    "basic_components/buffer/rtl" \
    "basic_components/gemv/rtl" \
    "basic_components/systolic_gemm_mxfp/rtl" \
    "basic_components/int_operation/rtl" \
    "basic_components/synopsis_ip_inst/rtl" \
    "basic_components/synopsis/rtl" \
    "memory/matrix_sram/rtl" \
    "memory/vector_sram/rtl" \
    "memory/scalar_sram/rtl" \
    "memory/HBM/rtl" \
    "memory/HBM/TileLink_Lib" \
    "memory/HBM/xilinx_ip" \
    "matrix_machine/rtl" \
    "frontend/rtl" \
    "scalar_machine/rtl" \
    "vector_machine/rtl" \
    "control/rtl" \
    "core/rtl" 
]


# Set search paths based on dir_list
lappend search_path ${src}
foreach dir $dir_list {
    lappend search_path "${src}/${dir}"
}


# Define files to skip (add Non-synthesisable files here)
set skip_list [list \
    "fp_rounding.sv" \
    "bram.sv" \
    "fake_hbm.sv" \
    "peripheral_system.sv" \
]


# Analyze all .sv and .v files in directories
foreach dir $dir_list {
    set full_path "${src}/${dir}"
    if {[file exists $full_path]} {
        # Search for both .sv and .v files
        set sv_files [glob -nocomplain "${full_path}/*.sv"]
        set v_files [glob -nocomplain "${full_path}/*.v"]
        set all_files [concat $sv_files $v_files]
        
        foreach file $all_files {
            set filename [file tail $file]
            
            # Check if file should be skipped
            if {[lsearch $skip_list $filename] >= 0} {
                puts "Skipping: $filename (in skip list)"
                continue
            }
            
            puts "Analyzing: $filename"
            # Use appropriate format based on file extension
            if {[string match "*.sv" $file]} {
                analyze -f sverilog -lib work $file
            } else {
                analyze -f verilog -lib work $file
            }
        }
    }
}

#------------------------------
# Elaborate
#------------------------------
puts "\n=== Elaborate ==="
elaborate ${top_design}