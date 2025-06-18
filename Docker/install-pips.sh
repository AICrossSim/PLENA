#!/usr/bin/env bash
# --------------------------------------------------------------------
#    This script installs pip packages for both Docker containers
# --------------------------------------------------------------------
# set -o errexit
# set -o pipefail
# set -o nounset

cd /workspace

python3 -m venv .coprocessor_env
source .coprocessor_env/bin/activate
pip install -e .