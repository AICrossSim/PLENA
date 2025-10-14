# Synthesis on DC

## Directory Structure
```
synopsys/
├── .synopsys_dc.setup      # DC setup (lib path, etc.)
└── analyzed/WORK/          # DC working database (*.pvl, *.syn, *.mr, cksum_dir)
└── outputs/
    ├── netlist/            # Synthesis netlists and timing files
    ├── reports/            # Analysis and timing reports
    └── logs/               # Runtime logs
└── constraints/
    ├── top_constraints.sdc # constrain file for top module: coprocessor
└── debug.tcl               # Tcl script for debugging purposes
└── run_debug.sh            # Bash script to run the debug.tcl
└── dc.tcl                  # Tcl script for synthesis
└── run_dc.sh               # Bash script to run the dc.tcl
└── module_dc.tcl           # Tcl script for module level synthesis
└── module_dc_run.sh        # Bash script to run the module_dc.tcl
└── module_debug.tcl        # Tcl script for module level debugging
└── module_debug_run.sh    # Bash script to run the module_debug.tcl
```
## Usage
Every time you need to cd into the synopsys directory.
```
cd tools/synopsys
```
If you want to run the unit level synthesis, you can run the module_dc.tcl script.
Every time you will need to modify the module_dc.tcl script to include the module you want to synthesize. Note: it would be better to truncate the src directory to only include the module you want to synthesize or the possible bugs from other modules will be caught and stop the synthesis process.

## Run debug (Check only)
Some of the bugs in the design will not be caught by the synthesis. This script will run the debug.tcl script, which is used to check the design. The bug information will be saved in the outputs/logs/debug.log file.
```
bash run_debug.sh
```

## Run synthesis
```
bash run_dc.sh
```
