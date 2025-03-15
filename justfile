# justfile for managing environment
set shell := ["bash", "-cu"]

# Set PYTHONPATH for current session
set-pythonpath:
    export PYTHONPATH="/home/george/Coprocessor_for_Llama/tools"
    echo "PYTHONPATH set to: $PYTHONPATH"

# Set PYTHONPATH and launch Python
python:
    export PYTHONPATH="/home/george/Coprocessor_for_Llama/tools"
    python

# Verify PYTHONPATH
check-pythonpath:
    echo "PYTHONPATH is: $PYTHONPATH"

# Remove __pycache__ to avoid import issues
clean:
    rm -rf /home/george/Coprocessor_for_Llama/tools/cfl_cocotb/__pycache__
    echo "Removed __pycache__"
