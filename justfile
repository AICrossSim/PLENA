alias ts := test-sw
alias th := test-hw
alias build := build-docker
alias sh := shell
# alias re := reformat


build-docker:
	docker build -f Docker/dockerfile-local --tag coprocessor-llama Docker

shell:
	docker run -it --shm-size 256m \
        --hostname coprocessor-llama \
        -w /workspace \
        -v /$(USER_PREFIX)/$(shell whoami)/.ssh:/root/.ssh \
        -v $(shell pwd):/workspace:z \
	    coprocessor-llama
        # -v /$(USER_PREFIX)/$(shell whoami)/.gitconfig:/root/.gitconfig \
        #coprocessor-llama /bin/bash -c "source .coprocessor_env/bin/activate && /bin/bash"


clean:
	@rm -rf *.log *.jou *.str

instruction_level_testing: 

test-hw:
	python3 src/basic_components/fp_operation/test/fp_ieee_partition_tb.py
	python3 src/basic_components/fp_operation/test/fp_ieee_normalize_tb.py
	python3 src/basic_components/fp_operation/test/fp_ieee_casting_tb.py
	python3 src/basic_components/fp_operation/test/fp_adder_tb.py
	python3 src/basic_components/fp_operation/test/fp_mult_tb.py
	python3 src/basic_components/fp_operation/test/fp_cp_adder_v2_tb.py
	python3 src/basic_components/fp_operation/test/fp_cp_mult_tb.py
	python3 src/basic_components/fp_operation/test/fp_cp_reciprocal_tb.py
	python3 src/basic_components/fp_operation/test/fp_reciprocal_tb.py
	python3 src/basic_components/fp_operation/test/fp_exp_tb.py
	python3 src/basic_components/fp_operation/test/fp_cp_exp_tb.py

test-sw:
	python3 tools/quant/quant_operations/sqrt.py
	python3 tools/quant/quant_operations/reciprocal.py

# test-sw:
# 	# cmd line interface is no longer supported
# 	# bash scripts/test-machop.sh
# 	pytest --log-level=DEBUG --verbose \
# 		-n 1 \
# 		--cov=src/chop/ --cov-report=html \
# 		--html=report.html --self-contained-html \
# 		--junitxml=test/report.xml \
# 		--profile --profile-svg \
# 		test/


# # This test will test all the available component
reformat:
	# format python files
	black *.py
	black src/chop
	black src/mase_components
	black src/mase_cocotb
	black test
	# format verilog
	# find src/mase_components -name '*.sv' -exec verible-verilog-format --inplace {} +;