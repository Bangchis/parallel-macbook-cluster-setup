#!/usr/bin/env bash
set -euo pipefail

L="${ATTN_L:-1024}"
for Br in ${ATTN_BR_LIST:-8 16 32 64}; do
  for Bc in ${ATTN_BC_LIST:-32 64 128 256}; do
    echo
    echo "BLOCKSIZE Br=$Br Bc=$Bc L=$L"
    ATTN_L="$L" \
    ATTN_BR="$Br" \
    ATTN_BC="$Bc" \
    ATTN_VERIFY=0 \
    ATTN_RUN_ID="block_Br${Br}_Bc${Bc}_L${L}" \
    ATTN_OUTPUT=results/raw/blocksize.csv \
    bash scripts/run_single_benchmark.sh
  done
done
