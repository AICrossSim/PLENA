set shell := ["bash", "-cu"]

# Define the project root as the directory containing the justfile
ROOT := "{{justfile() | dirname}}"

set-pythonpath:
    export PYTHONPATH="/Users/georgewu/Documents/Cambridge/Coprocessor_for_Llama/tools"
    echo "PYTHONPATH set to: $PYTHONPATH"
    
python:
    export PYTHONPATH="${ROOT}/tools"
    cd "${ROOT}" && python

check-pythonpath:
    export PYTHONPATH="${ROOT}/tools"
    echo "PYTHONPATH is: $PYTHONPATH"

clean:
    rm -rf "${ROOT}/tools/cfl_cocotb/__pycache__"
    echo "Removed __pycache__"
