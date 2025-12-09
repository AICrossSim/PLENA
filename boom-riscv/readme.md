## [BOOM](https://github.com/riscv-boom/riscv-boom)

### Setup
```git clone https://github.com/ucb-bar/chipyard.git``` \
```git checkout 1.12.3``` \
```cd chipyard``` \
```./build-setup.sh riscv-tools``` \
```source env.sh``` \
Benchmark Execution \
```cd sims/verilator``` \
```make run-binary CONFIG=MediumBoomV3Config BINARY=../../toolchains/riscv-tools/riscv-tests/build/benchmarks/dhrystone.riscv```


|Benchmark | Minstret |
|----------|----------|
|dhrystone | 186031   |
|median    | 4659     |
|memcpy    | 5525     |
|mm        | 24744    |
|mt-matmul | 30325    |
|mt-memcpy | 14674    |
|mt-vvadd  | 20824    |
|multiply  | 42503    |
|pmp       | None     |
|qsort     | 123506   |
|rsort     | 171154   |
|spmv      | 34466    |
|towers    | 4562     |
|vec-daxpy | Failed   |
|vec-memcpy| Failed   |
|vec-sgemm | Not Know |
|vec-strcmp| Not Know |
|vvadd     | 2416     |