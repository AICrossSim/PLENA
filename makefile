.PHONY: test

# Export the PYTHONPATH environment variable so that it is set for any commands run by Make.
export PYTHONPATH := /home/hw1020/Documents/ARIA/Coprocessor_for_Llama/src/ac_cocotb:$(PYTHONPATH)

# The 'test' target runs the Python test script.
test:
	python3 matrix_machine/test/matmul_tb.py
