#!/usr/bin/env bash
set -euo pipefail

run_dir="${ATTN_RUN_DIR:-results}"
evidence_dir="${ATTN_EVIDENCE_DIR:-$run_dir/evidence}"
mkdir -p "$evidence_dir"

log="$evidence_dir/cluster_evidence.txt"
hostfile="${ATTN_HOSTFILE:-configs/hosts}"
use_hostfile="${ATTN_USE_HOSTFILE:-1}"
np="${ATTN_EVIDENCE_NP:-3}"

run_cmd() {
  {
    echo
    echo "COMMAND: $*"
    "$@"
  } >> "$log" 2>&1 || {
    local code=$?
    {
      echo "COMMAND_FAILED exit_code=$code"
    } >> "$log" 2>&1
    return 0
  }
}

{
  echo "FINAL_CLUSTER_EVIDENCE"
  date -u +"utc_time=%Y-%m-%dT%H:%M:%SZ"
  echo "repo=$(pwd)"
  echo "run_dir=$run_dir"
  echo "evidence_dir=$evidence_dir"
  echo "hostfile=$hostfile"
  echo "use_hostfile=$use_hostfile"
  echo "evidence_np=$np"
} > "$log"

run_cmd hostname
run_cmd sh -c 'hostname -I 2>/dev/null || ip -4 addr show 2>/dev/null || ifconfig 2>/dev/null'
run_cmd uname -a
if command -v nproc >/dev/null 2>&1; then
  run_cmd nproc
elif command -v sysctl >/dev/null 2>&1; then
  run_cmd sysctl -n hw.physicalcpu
fi
if command -v lscpu >/dev/null 2>&1; then
  run_cmd lscpu
fi
run_cmd git rev-parse HEAD
run_cmd git status -sb
run_cmd which mpirun
run_cmd mpirun --version
run_cmd which mpicc
run_cmd mpicc --version
run_cmd bash scripts/build.sh

if [[ "$use_hostfile" == "1" && -f "$hostfile" ]]; then
  cp "$hostfile" "$evidence_dir/hosts.used"
  python3 scripts/summarize_host_slots.py \
    --hostfile "$hostfile" \
    --output "$evidence_dir/host_slots.csv" \
    --summary "$evidence_dir/host_slots.env" >> "$log" 2>&1 || true
  {
    echo
    echo "HOSTFILE_CONTENT"
    cat "$hostfile"
    echo
    echo "HOST_SLOTS_SUMMARY"
    cat "$evidence_dir/host_slots.env" 2>/dev/null || true
  } >> "$log"
elif [[ "$use_hostfile" != "1" ]]; then
  echo "$(hostname) slots=$np" > "$evidence_dir/hosts.used"
  python3 scripts/summarize_host_slots.py \
    --hostfile "$evidence_dir/hosts.used" \
    --output "$evidence_dir/host_slots.csv" \
    --summary "$evidence_dir/host_slots.env" >> "$log" 2>&1 || true
  {
    echo
    echo "HOSTFILE_CONTENT"
    cat "$evidence_dir/hosts.used"
    echo
    echo "HOST_SLOTS_SUMMARY"
    cat "$evidence_dir/host_slots.env" 2>/dev/null || true
  } >> "$log"
else
  echo "HOSTFILE_MISSING=$hostfile" >> "$log"
fi

mpi=(mpirun -np "$np")
if [[ -n "${MPI_MAP_BY:-}" ]]; then
  mpi+=(--map-by "$MPI_MAP_BY")
fi
if [[ "$use_hostfile" == "1" ]]; then
  mpi+=(--hostfile "$hostfile")
  mpi+=(--mca btl tcp,self --mca btl_tcp_if_include "${MPI_LAN_CIDR:-192.168.31.0/24}" --mca btl_tcp_disable_family 6)
else
  mpi+=(--oversubscribe --mca btl self,sm,tcp)
fi

run_cmd "${mpi[@]}" hostname

{
  echo
  echo "EVIDENCE_DONE=YES"
  echo "EVIDENCE_LOG=$log"
} >> "$log"

echo "EVIDENCE_LOG=$log"
