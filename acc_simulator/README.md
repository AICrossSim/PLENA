From the **project root**:

### Installation

```bash
conda env create -f acc_simulator/environment.yml
conda activate acc-sim
git submodule update --init --recursive
cd acc_simulator/third_party
cd fast_hadamard_transform
pip install -e .
```

### Installation
```bash
bash acc_simulator/run_acc_sim_job.sh
```