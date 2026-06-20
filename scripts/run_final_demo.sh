#!/usr/bin/env bash
set -euo pipefail

config_file="${ATTN_EXPERIMENT_ENV:-configs/attention_experiment.env}"
if [[ -f "$config_file" ]]; then
  # shellcheck disable=SC1090
  source "$config_file"
else
  echo "CONFIG_NOTE: $config_file not found; using demo defaults."
fi

timestamp="$(date +%Y%m%d-%H%M%S)"
run_dir="${ATTN_DEMO_DIR:-results/demo_${timestamp}}"
raw_dir="$run_dir/raw"
evidence_dir="$run_dir/evidence"
mkdir -p "$raw_dir" "$evidence_dir"

np="${ATTN_DEMO_NP:-${ATTN_EVIDENCE_NP:-3}}"
hostfile="${ATTN_HOSTFILE:-configs/hosts}"
use_hostfile="${ATTN_USE_HOSTFILE:-1}"
mpi_lan_cidr="${MPI_LAN_CIDR:-192.168.31.0/24}"
log_file="$run_dir/demo_terminal.log"

required_hosts=()
if [[ "$use_hostfile" == "1" && -f "$hostfile" ]]; then
  while read -r host _; do
    if [[ -n "${host:-}" && "$host" != \#* ]]; then
      required_hosts+=("$host")
    fi
  done < "$hostfile"
fi

summary_args=(--run-dir "$run_dir")
for host in "${required_hosts[@]}"; do
  summary_args+=(--require-host "$host")
done

{
  echo "FINAL_DEMO_RUN"
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  echo "run_dir=$run_dir"
  echo "config_file=$config_file"
  echo "np=$np"
  echo "use_hostfile=$use_hostfile"
  echo "hostfile=$hostfile"
  echo "mpi_lan_cidr=$mpi_lan_cidr"
  echo "git_commit=$(git rev-parse --short HEAD 2>/dev/null || true)"
  echo

  echo "PHASE 1/4: preflight"
  if [[ -f "$config_file" ]]; then
    python3 scripts/check_experiment_config.py --config "$config_file" --output "$run_dir/preflight.md"
  else
    python3 scripts/check_experiment_config.py --output "$run_dir/preflight.md"
  fi
  echo

  echo "PHASE 2/4: build"
  bash scripts/build.sh
  echo

  echo "PHASE 3/4: MPI hostnames"
  if [[ "$use_hostfile" == "1" ]]; then
    mpi_hostname=(mpirun -np "$np" --hostfile "$hostfile")
    mpi_hostname+=(--mca btl tcp,self --mca btl_tcp_if_include "$mpi_lan_cidr" --mca btl_tcp_disable_family 6)
  else
    mpi_hostname=(mpirun -np "$np" --oversubscribe --mca btl self,sm,tcp)
  fi
  echo "COMMAND: ${mpi_hostname[*]} hostname"
  "${mpi_hostname[@]}" hostname | tee "$evidence_dir/mpi_hostname.txt"
  echo

  echo "PHASE 4/4: correctness and rank work"
  ATTN_RESULTS_DIR="$raw_dir" \
  ATTN_NP="$np" \
  ATTN_USE_HOSTFILE="$use_hostfile" \
  ATTN_HOSTFILE="$hostfile" \
  MPI_LAN_CIDR="$mpi_lan_cidr" \
  ATTN_ALGO="${ATTN_DEMO_ALGO:-${ATTN_ALGO:-mpi_online}}" \
  ATTN_THREADS="${ATTN_DEMO_THREADS:-${ATTN_THREADS:-1}}" \
  ATTN_B="${ATTN_DEMO_B:-${ATTN_B:-1}}" \
  ATTN_H="${ATTN_DEMO_H:-2}" \
  ATTN_L="${ATTN_DEMO_L:-64}" \
  ATTN_DH="${ATTN_DEMO_DH:-32}" \
  ATTN_BR="${ATTN_DEMO_BR:-16}" \
  ATTN_BC="${ATTN_DEMO_BC:-64}" \
  ATTN_VERIFY=1 \
  ATTN_DEBUG=1 \
  bash scripts/run_demo_correctness.sh
  echo

  python3 scripts/summarize_demo_run.py "${summary_args[@]}"
  echo "FINAL_DEMO_DONE=YES"
  echo "DEMO_DIR=$run_dir"
} | tee "$log_file"
