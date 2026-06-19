#!/usr/bin/env bash
set -euo pipefail

L="${ATTN_L:-1024}"
for P in 1 2 4 8 12; do
  echo
  echo "SPEEDUP P=$P L=$L"
  ATTN_NP="$P" \
  ATTN_L="$L" \
  ATTN_VERIFY=0 \
  ATTN_RUN_ID="speedup_P${P}_L${L}" \
  ATTN_OUTPUT=results/raw/speedup.csv \
  bash scripts/run_single_benchmark.sh
done
