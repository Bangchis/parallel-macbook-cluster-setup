#!/usr/bin/env bash
set -euo pipefail

L="${ATTN_L:-1024}"
results_dir="${ATTN_RESULTS_DIR:-results/raw}"
for threads in ${ATTN_THREAD_LIST:-1 2 4}; do
  echo
  echo "THREAD_SWEEP threads=$threads L=$L"
  ATTN_THREADS="$threads" \
  ATTN_L="$L" \
  ATTN_VERIFY="${ATTN_VERIFY:-0}" \
  ATTN_RUN_ID="threads_T${threads}_L${L}" \
  ATTN_OUTPUT="$results_dir/thread_scaling.csv" \
  bash scripts/run_single_benchmark.sh
done
