#!/usr/bin/env bash
set -euo pipefail

export ATTN_ALGO="${ATTN_ALGO:-mpi_online}"
export ATTN_NP="${ATTN_NP:-12}"
export ATTN_B=1
export ATTN_H=8
export ATTN_L="${ATTN_L:-1024}"
export ATTN_DH=64
export ATTN_BR=32
export ATTN_BC=64
export ATTN_CAUSAL=0
export ATTN_ASSIGNMENT=block_cyclic
export ATTN_SCHEDULE=static
export ATTN_THREADS="${ATTN_THREADS:-1}"
export ATTN_VERIFY=0
export ATTN_DEBUG=0
export ATTN_RUN_ID=demo_perf
export ATTN_OUTPUT=results/raw/demo_perf.csv

bash scripts/run_single_benchmark.sh
