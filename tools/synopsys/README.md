# Synthesis on DC

## Directory Structure
```
syn/
├── analyzed/WORK/    # DC working database (*.pvl, *.syn, *.mr, cksum_dir)
└── outputs/
    ├── netlist/      # Synthesis netlists and timing files
    ├── reports/      # Analysis and timing reports
    └── logs/         # Runtime logs
└── debug.tcl         # Tcl script for debug purpose
└── run_debug.sh      # Bash script to run the debug_rtl.tcl
```

## Run debug (Check only)
```
bash run_debug.sh
```
