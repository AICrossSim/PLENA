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
└── module_debug.tcl        # Tcl script for module level debugging
└── dc.tcl                  # Tcl script for synthesis
└── module_dc.tcl           # Tcl script for module level synthesis
```
## Usage
Before running the synthesis, you will need to cd into the synopsys directory.
```
cd <path to the project>/tools/synopsys
```
`module_dc.tcl` and `run_module_dc.sh` are used to run the unit level synthesis.
`dc.tcl` and `run_dc.sh` are used to run the top level synthesis.

For unit level synthesis, every time you will need to modify the `module_dc.tcl` script to include the module you want to synthesize. 

**Note**: It would be better to link the src directory to and only to the related module. Or the possible bugs from other modules will be caught and stop the synthesis process.

### Run debug (Check only)
```
bash run_debug.sh
```

### Run synthesis
```
bash run_dc.sh
```
