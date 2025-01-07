#!/bin/bash

# This script assumes we are running in a Miniconda container where:
# - /opt/conda is the Miniconda or Miniforge installation directory
# - https://github.com/conda/conda is mounted at /workspaces/conda
# - https://github.com/conda/conda-classic-solver is mounted at
#   /workspaces/conda-classic-solver

set -euo pipefail

BASE_CONDA=${BASE_CONDA:-/opt/conda}
SRC_CONDA=${SRC_CONDA:-/workspaces/conda}
SRC_CONDA_CLASSIC_SOLVER=${SRC_CONDA_CLASSIC_SOLVER:-/workspaces/conda-classic-solver}

cd "$SRC_CONDA"
echo "Initializing conda in dev mode..."
"$BASE_CONDA/bin/python" -m conda init --dev bash
cd -

echo "Installing conda-classic-solver in dev mode..."
"$BASE_CONDA/bin/python" -m pip install -e "$SRC_CONDA_CLASSIC_SOLVER" --no-deps

set -x
conda list -p "$BASE_CONDA"
conda info
conda config --show-sources
set +x
