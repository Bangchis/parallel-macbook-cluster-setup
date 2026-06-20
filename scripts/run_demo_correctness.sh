#!/usr/bin/env bash
set -euo pipefail

results_dir="${ATTN_RESULTS_DIR:-results/raw}"
export ATTN_ALGO="${ATTN_ALGO:-mpi_online}"
export ATTN_NP="${ATTN_NP:-3}"
export ATTN_B="${ATTN_B:-1}"
export ATTN_H="${ATTN_H:-2}"
export ATTN_L="${ATTN_L:-64}"
export ATTN_DH="${ATTN_DH:-32}"
export ATTN_BR="${ATTN_BR:-16}"
export ATTN_BC="${ATTN_BC:-64}"
export ATTN_CAUSAL="${ATTN_CAUSAL:-0}"
export ATTN_ASSIGNMENT="${ATTN_ASSIGNMENT:-block_cyclic}"
export ATTN_SCHEDULE="${ATTN_SCHEDULE:-static}"
export ATTN_THREADS="${ATTN_THREADS:-2}"
export ATTN_VERIFY=1
export ATTN_DEBUG=1
export ATTN_RUN_ID=demo_correctness
export ATTN_OUTPUT="$results_dir/demo_correctness.csv"

bash scripts/run_single_benchmark.sh
