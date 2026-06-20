#!/usr/bin/env bash
set -euo pipefail

bash scripts/run_demo_correctness.sh
bash scripts/run_find_N.sh
bash scripts/run_granularity_sweep.sh
bash scripts/run_speedup_sweep.sh
bash scripts/run_blocksize_sweep.sh
bash scripts/run_memory_comparison.sh
bash scripts/run_comm_strategy_sweep.sh
bash scripts/run_demo_perf.sh

echo "ALL_EXPERIMENTS_DONE=YES"
