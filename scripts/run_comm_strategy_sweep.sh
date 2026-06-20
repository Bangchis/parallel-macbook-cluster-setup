#!/usr/bin/env bash
set -euo pipefail

L="${ATTN_L:-1024}"
for algo in ${ATTN_ALGO_LIST:-mpi_online mpi_online_nb}; do
  echo
  echo "COMM_STRATEGY algo=$algo L=$L"
  ATTN_ALGO="$algo" \
  ATTN_L="$L" \
  ATTN_VERIFY="${ATTN_VERIFY:-0}" \
  ATTN_RUN_ID="comm_${algo}_L${L}" \
  ATTN_OUTPUT=results/raw/comm_strategy.csv \
  bash scripts/run_single_benchmark.sh
done
