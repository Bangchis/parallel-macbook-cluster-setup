#!/usr/bin/env bash
set -euo pipefail

plot_python="${PLOT_PYTHON:-.venv-plot/bin/python}"
if [[ ! -x "$plot_python" ]]; then
  echo "Plot environment missing. Run: bash scripts/install_plot_deps.sh"
  exit 1
fi

raw_dir="${ATTN_RESULTS_DIR:-results/raw}"
figures_dir="${ATTN_FIGURES_DIR:-results/figures}"
tables_dir="${ATTN_TABLES_DIR:-results/tables}"

"$plot_python" plots/plot_all.py --input "$raw_dir" --output "$figures_dir"
python3 scripts/make_report_tables.py --input "$raw_dir" --output "$tables_dir"
python3 scripts/analyze_final_results.py --input "$raw_dir" --output "$tables_dir/analysis.md"

run_dir="$(dirname "$raw_dir")"
if [[ -d "$run_dir" && "$run_dir" != "." ]]; then
  python3 scripts/generate_final_report_draft.py \
    --run-dir "$run_dir" \
    --output "$run_dir/report/final_report_draft.md"
fi

echo "REPORT_ARTIFACTS_DONE=YES"
