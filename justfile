# Not in used at the moment.

set shell := ["bash", "-cu"]

ROOT := "{{justfile() | dirname}}"

set-pythonpath:
    export PYTHONPATH="/Users/georgewu/Documents/Cambridge/Coprocessor_for_Llama/tools"
    echo "PYTHONPATH set to: $PYTHONPATH"
    
python:
    export PYTHONPATH="${ROOT}/tools"
    cd "${ROOT}" && python
