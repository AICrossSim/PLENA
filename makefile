# Export PYTHONPATH globally
export PYTHONPATH := /home/hw1020/Documents/ARIA/Coprocessor_for_Llama/src/ac_cocotb:$(PYTHONPATH)

# Define a rule
initial:
	@echo "PYTHONPATH is set to: $(PYTHONPATH)"


# The 'test' target runs the Python test script.
test:
	python3 matrix_machine/test/matmul_tb.py
