#!/usr/bin/env bash
set -euo pipefail

for L in 512 1024 1536 2048 3072 4096; do
  echo
  echo "FIND_N L=$L"
  ATTN_L="$L" \
  ATTN_H="${ATTN_H:-8}" \
  ATTN_DH="${ATTN_DH:-64}" \
  ATTN_VERIFY=0 \
  ATTN_RUN_ID="find_N_L${L}" \
  ATTN_OUTPUT=results/raw/find_N.csv \
  bash scripts/run_single_benchmark.sh
done
