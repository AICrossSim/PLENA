# Configure your environment

```
make build-docker
```

This will help you to download the required non-python related packages for the tool like clang, llvm, verilator, etc.

# install dependencies

```
make shell
```
This command cd into the shell of the docker container.

```
python3 -m venv .coprocessor_env
source .coprocessor_env/bin/activate
pip install -e .
```

The Python environment will be installed locally, allowing you to customize it according to your specific needs

<!-- ```bash --> -->
