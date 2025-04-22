from setuptools import setup, find_packages

setup(
    name='cfl_cocotb',  
    version='1.0',  # random
    packages=find_packages("tools"),
    package_dir={'': 'tools'},
    install_requires=[
        'black', 'toml', 'GitPython', 'colorlog', 'cocotb[bus]==1.9.2',
        'pytest', 'pytorch-lightning', 'transformers', 
        'timm', 'pytorch-nlp', 'datasets', 'ipython', 'ipdb',
        'sentencepiece', 'einops', 'deepspeed', 'pybind11',
        'tabulate', 'tensorboardx', 'hyperopt', 'accelerate',
        'optuna', 'stable-baselines3[extra]', 'h5py', 'scikit-learn',
        'scipy', 'onnxruntime', 'matplotlib', 'sphinx-rtd-theme',
        'imageio', 'imageio-ffmpeg', 'opencv-python', 'kornia',
        'ghp-import', 'optimum', 'pytest-profiling', 'myst_parser',
        'pytest-cov', 'pytest-xdist', 'pytest-sugar', 'pytest-html',
        'lightning', 'wandb', 'bitarray', 'bitstring', 'emoji',
        'numpy<2.0', 'tensorboard',
        'absl-py', 'sphinx-glpi-theme', 'prettytable'
    ]
)