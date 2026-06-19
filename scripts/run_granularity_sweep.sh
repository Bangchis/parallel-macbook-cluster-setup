#!/usr/bin/env bash
set -euo pipefail

L="${ATTN_L:-1024}"
for assignment in contiguous cyclic block_cyclic; do
  for Br in 1 8 16 32 64; do
    echo
    echo "GRANULARITY assignment=$assignment Br=$Br L=$L"
    ATTN_L="$L" \
    ATTN_BR="$Br" \
    ATTN_ASSIGNMENT="$assignment" \
    ATTN_VERIFY=0 \
    ATTN_RUN_ID="gran_${assignment}_Br${Br}_L${L}" \
    ATTN_OUTPUT=results/raw/granularity.csv \
    bash scripts/run_single_benchmark.sh
  done
done
