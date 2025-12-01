From the **project root**:

### Installation

```bash
conda env create -f acc_simulator/environment.yml
conda activate acc-sim
git submodule update --init --recursive
cd acc_simulator/third_party
cd fast_hadamard_transform
pip install -e .

python -m pip install -e . --no-deps --no-build-isolation --config-settings editable_mode=compat -v

```

### Installation
```bash
bash acc_simulator/run_acc_sim_job.sh
```