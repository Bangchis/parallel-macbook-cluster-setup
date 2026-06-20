#!/usr/bin/env bash
set -euo pipefail

config_file="${ATTN_EXPERIMENT_ENV:-configs/attention_experiment.env}"
if [[ -f "$config_file" ]]; then
  # shellcheck disable=SC1090
  source "$config_file"
else
  echo "CONFIG_NOTE: $config_file not found; using built-in defaults."
  echo "Create it from configs/attention_experiment.env.example for the real cluster run."
fi

timestamp="$(date +%Y%m%d-%H%M%S)"
run_dir="${ATTN_RUN_DIR:-results/final_${timestamp}}"
export ATTN_RUN_DIR="$run_dir"
export ATTN_RESULTS_DIR="${ATTN_RESULTS_DIR:-$run_dir/raw}"
export ATTN_FIGURES_DIR="${ATTN_FIGURES_DIR:-$run_dir/figures}"
export ATTN_TABLES_DIR="${ATTN_TABLES_DIR:-$run_dir/tables}"
export ATTN_EVIDENCE_DIR="${ATTN_EVIDENCE_DIR:-$run_dir/evidence}"
mkdir -p "$ATTN_RESULTS_DIR" "$ATTN_FIGURES_DIR" "$ATTN_TABLES_DIR" "$ATTN_EVIDENCE_DIR"

total_procs="${ATTN_TOTAL_PROCS:-12}"
target_min_ms="${ATTN_TARGET_MIN_MS:-120000}"
target_max_ms="${ATTN_TARGET_MAX_MS:-180000}"

echo "FINAL_EXPERIMENT_RUN_DIR=$run_dir"
echo "RAW_RESULTS=$ATTN_RESULTS_DIR"
echo "FIGURES=$ATTN_FIGURES_DIR"
echo "TABLES=$ATTN_TABLES_DIR"
echo "EVIDENCE=$ATTN_EVIDENCE_DIR"

echo
echo "PHASE 1/7: cluster evidence"
bash scripts/collect_final_evidence.sh

echo
echo "PHASE 2/7: correctness demo"
ATTN_NP="$total_procs" \
ATTN_VERIFY=1 \
bash scripts/run_demo_correctness.sh

echo
echo "PHASE 3/7: find N with P=$total_procs"
ATTN_NP="$total_procs" \
ATTN_L_LIST="${ATTN_FIND_N_LIST:-512 1024 1536 2048 3072 4096}" \
bash scripts/run_find_N.sh

selected_n="${ATTN_SELECTED_N:-}"
if [[ -z "$selected_n" ]]; then
  selected_n="$(
    python3 scripts/select_N_from_csv.py \
      --input "$ATTN_RESULTS_DIR/find_N.csv" \
      --min-ms "$target_min_ms" \
      --max-ms "$target_max_ms" \
      --algorithm "${ATTN_ALGO:-mpi_online}" \
      --world-size "$total_procs" \
      --explain
  )"
fi

if [[ "$selected_n" -le 0 ]]; then
  echo "ERROR: selected N is invalid: $selected_n"
  exit 1
fi

speedup_l=$((selected_n * 2))
memory_l="${ATTN_MEMORY_L:-512}"
thread_np="${ATTN_THREAD_SWEEP_NP:-3}"

cat > "$run_dir/experiment_summary.env" <<EOF
ATTN_SELECTED_N=$selected_n
ATTN_SPEEDUP_L=$speedup_l
ATTN_TOTAL_PROCS=$total_procs
ATTN_TARGET_MIN_MS=$target_min_ms
ATTN_TARGET_MAX_MS=$target_max_ms
ATTN_RESULTS_DIR=$ATTN_RESULTS_DIR
ATTN_FIGURES_DIR=$ATTN_FIGURES_DIR
ATTN_TABLES_DIR=$ATTN_TABLES_DIR
ATTN_EVIDENCE_DIR=$ATTN_EVIDENCE_DIR
ATTN_THREAD_SWEEP_NP=$thread_np
EOF

echo "SELECTED_N=$selected_n"
echo "SPEEDUP_L_2N=$speedup_l"

echo
echo "PHASE 4/7: granularity and load balance at N=$selected_n"
ATTN_NP="$total_procs" \
ATTN_L="$selected_n" \
bash scripts/run_granularity_sweep.sh

echo
echo "PHASE 5/7: speedup at 2N=$speedup_l"
ATTN_L="$speedup_l" \
ATTN_P_LIST="${ATTN_P_LIST:-1 2 4 8 12}" \
bash scripts/run_speedup_sweep.sh

echo
echo "PHASE 6/7: block size, memory, communication, and OpenMP thread scaling"
ATTN_NP="$total_procs" \
ATTN_L="$selected_n" \
bash scripts/run_blocksize_sweep.sh

ATTN_NP="$total_procs" \
ATTN_L="$memory_l" \
ATTN_VERIFY=0 \
bash scripts/run_memory_comparison.sh

ATTN_NP="$total_procs" \
ATTN_L="$selected_n" \
bash scripts/run_comm_strategy_sweep.sh

MPI_MAP_BY="${ATTN_THREAD_SWEEP_MAP_BY:-}" \
ATTN_NP="$thread_np" \
ATTN_L="$selected_n" \
bash scripts/run_thread_sweep.sh

echo
echo "PHASE 7/7: report artifacts"
bash scripts/run_report_artifacts.sh
python3 scripts/check_final_readiness.py --run-dir "$run_dir"

echo "REQUIRED_EXPERIMENTS_DONE=YES"
echo "SUMMARY_FILE=$run_dir/experiment_summary.env"
