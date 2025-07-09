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
```

## Run debug (Check only)
```
bash run_debug.sh
```

## Run synthesis
```
bash run_dc.sh
```
