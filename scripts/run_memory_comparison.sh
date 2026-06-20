#!/usr/bin/env bash
set -euo pipefail

for algo in serial_full serial_row omp_online mpi_online; do
  echo
  echo "MEMORY algorithm=$algo"
  ATTN_ALGO="$algo" \
  ATTN_NP="${ATTN_NP:-1}" \
  ATTN_USE_HOSTFILE="${ATTN_USE_HOSTFILE:-0}" \
  ATTN_B="${ATTN_B:-1}" \
  ATTN_H="${ATTN_H:-2}" \
  ATTN_L="${ATTN_L:-128}" \
  ATTN_DH="${ATTN_DH:-32}" \
  ATTN_VERIFY="${ATTN_VERIFY:-1}" \
  ATTN_RUN_ID="memory_${algo}" \
  ATTN_OUTPUT=results/raw/memory.csv \
  bash scripts/run_single_benchmark.sh
done
