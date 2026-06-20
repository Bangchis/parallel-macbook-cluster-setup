#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv-plot
.venv-plot/bin/python -m pip install --upgrade pip
.venv-plot/bin/python -m pip install pandas matplotlib
echo "PLOT_DEPS_READY=YES"
echo "Use: .venv-plot/bin/python plots/plot_all.py --input results/raw --output results/figures"
