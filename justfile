alias ts := test-sw
alias th := test-hw

test-hw:
    python3 src/basic_components/fp_operation/test/fp_ieee_partition_tb.py
    python3 src/basic_components/fp_operation/test/fp_ieee_normalize_tb.py
    # python3 src/basic_components/fp_operation/test/fp_ieee_casting_tb.py
    python3 src/basic_components/fp_operation/test/fp_cp_adder_tb.py
    python3 src/basic_components/fp_operation/test/fp_cp_mult_tb.py
    # python3 src/basic_components/fp_operation/test/fp_cp_asym_mult_tb.py

    # python3 src/basic_components/fp_operation/test/fp_reciprocal_tb.py
    # python3 src/basic_components/fp_operation/test/fp_exp_tb.py
    # python3 src/basic_components/fp_operation/test/fp_cp_reciprocal_tb.py
    # python3 src/basic_components/fp_operation/test/fp_cp_exp_tb.py

    python3 src/basic_components/fp_operation/test/fp_fix_reciprocal_tb.py
    python3 src/basic_components/fp_operation/test/fp_fix_exp_tb.py
    python3 src/basic_components/fp_operation/test/fp_fix_adder_tb.py
    python3 src/basic_components/fp_operation/test/fp_fix_mult_tb.py

test-sw:
    python3 tools/quant/quant_operations/sqrt.py
    python3 tools/quant/quant_operations/reciprocal.py

build-env arg:
    # cd behave_simulator
    python3 src/system/sys_utils/build_env.py {{arg}}

reformat:
    black *.py
    black src/chop
    black src/mase_components
    black src/mase_cocotb
    black test
    # find src/mase_components -name '*.sv' -exec verible-verilog-format --inplace {} +;