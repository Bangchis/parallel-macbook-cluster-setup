#!/usr/bin/env bash
set -euo pipefail

if [[ ! -x ".venv-plot/bin/python" ]]; then
  echo "Missing plot environment. Run first:"
  echo "  bash scripts/install_plot_deps.sh"
  exit 1
fi

timestamp="$(date +%Y%m%d-%H%M%S)"
export ATTN_RUN_DIR="${ATTN_RUN_DIR:-results/local_final_smoke_${timestamp}}"
export ATTN_USE_HOSTFILE=0
export ATTN_EVIDENCE_NP=1
export ATTN_TOTAL_PROCS=1
export ATTN_P_LIST="1"
export ATTN_FIND_N_LIST="16"
export ATTN_ASSIGNMENT_LIST="block_cyclic"
export ATTN_BR_LIST="8"
export ATTN_BC_LIST="16"
export ATTN_MEMORY_L=16
export ATTN_THREAD_SWEEP_NP=1
export ATTN_THREAD_LIST="1 2"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/matplotlib-cache}"

bash scripts/run_required_experiments.sh

python3 scripts/check_final_readiness.py --run-dir "$ATTN_RUN_DIR"

echo "LOCAL_FINAL_SMOKE_DONE=YES"
echo "LOCAL_FINAL_SMOKE_DIR=$ATTN_RUN_DIR"
