#!/usr/bin/env bash
set -euo pipefail

plot_python="${PLOT_PYTHON:-.venv-plot/bin/python}"
if [[ ! -x "$plot_python" ]]; then
  echo "Plot environment missing. Run: bash scripts/install_plot_deps.sh"
  exit 1
fi

"$plot_python" plots/plot_all.py --input results/raw --output results/figures
python3 scripts/make_report_tables.py --input results/raw --output results/tables

echo "REPORT_ARTIFACTS_DONE=YES"
