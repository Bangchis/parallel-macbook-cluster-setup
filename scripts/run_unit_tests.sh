#!/usr/bin/env bash
set -euo pipefail

export OMPI_MCA_btl="${OMPI_MCA_btl:-self}"

bash scripts/build.sh

run_case() {
  local name="$1"
  shift
  echo
  echo "CASE $name"
  "$@"
}

run_check() {
  local algo="$1"
  local B="$2"
  local H="$3"
  local L="$4"
  local Dh="$5"
  local causal="$6"
  run_case "${algo}_B${B}_H${H}_L${L}_Dh${Dh}_causal${causal}" \
    ./build/attention_bench \
      --algo "$algo" \
      --B "$B" --H "$H" --L "$L" --Dh "$Dh" \
      --Br 8 --Bc 16 \
      --causal "$causal" \
      --schedule static \
      --omp_threads 2 \
      --verify 1 \
      --debug 0 \
      --run_id "unit_${algo}_${B}_${H}_${L}_${Dh}_${causal}" \
      --output results/raw/unit_summary.csv
}

for causal in 0 1; do
  for algo in serial_full serial_row omp_row omp_online mpi_row mpi_online mpi_row_nb mpi_online_nb; do
    run_check "$algo" 1 1 4 4 "$causal"
    run_check "$algo" 1 2 16 8 "$causal"
    run_check "$algo" 2 2 64 32 "$causal"
  done
done

echo
echo "CORRECTNESS_PASS=YES"
