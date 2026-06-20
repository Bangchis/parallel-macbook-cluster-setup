#!/usr/bin/env bash
set -euo pipefail

L="${ATTN_L:-1024}"
results_dir="${ATTN_RESULTS_DIR:-results/raw}"
for assignment in ${ATTN_ASSIGNMENT_LIST:-contiguous cyclic block_cyclic}; do
  for Br in ${ATTN_BR_LIST:-1 8 16 32 64}; do
    echo
    echo "GRANULARITY assignment=$assignment Br=$Br L=$L"
    ATTN_L="$L" \
    ATTN_BR="$Br" \
    ATTN_ASSIGNMENT="$assignment" \
    ATTN_VERIFY=0 \
    ATTN_RUN_ID="gran_${assignment}_Br${Br}_L${L}" \
    ATTN_OUTPUT="$results_dir/granularity.csv" \
    bash scripts/run_single_benchmark.sh
  done
done
