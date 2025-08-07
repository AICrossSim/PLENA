## Steps to run the example testing code.

- cp the synopsys ip from the dw library/mnt/applications/synopsys/2024-25/RHELx86/SYN_2024.09-SP2/dw/ to the our repo /src/basic_component/synopsys directory
- Build the docker
- make shell
- source .coprocessor_env/bin/activate
- python3 src/system/test/SimTop_tb.py --path test/Instr_Level_Benchmark/vector_fp_add.asm

# 