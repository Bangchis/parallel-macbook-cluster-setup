#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
workspace="${1:-/shared/mpi}"
hostfile="${2:-$workspace/hosts_all_1slot}"
np="${MPI_TEST_NP:-3}"
mpi_lan_cidr="${MPI_LAN_CIDR:-${LAN_SUBNET:-192.168.31.0/24}}"
timestamp="$(date +%Y%m%d-%H%M%S)"
results_dir="${RESULTS_DIR:-$workspace/results/$timestamp-parallel-unit-tests}"
log_file="$results_dir/parallel_unit_tests.log"

mpi_common=(
  --mca btl tcp,self
  --mca btl_tcp_if_include "$mpi_lan_cidr"
  --mca btl_tcp_disable_family 6
)

if [[ ! -f "$hostfile" ]]; then
  echo "Missing hostfile: $hostfile" >&2
  echo "Run scripts/reconnect_after_lan_change.sh first, or create hosts_all_1slot." >&2
  exit 1
fi

mkdir -p "$workspace" "$results_dir"
cp "$repo_root/mpi_samples/parallel_unit_tests.c" "$workspace/parallel_unit_tests.c"

cd "$workspace"
mpicc -std=c11 -Wall -Wextra -O2 parallel_unit_tests.c -o parallel_unit_tests

{
  echo "PARALLEL_UNIT_TEST_RUN"
  date -Is
  echo "runner_hostname=$(hostname)"
  echo "runner_ips=$(hostname -I)"
  echo "workspace=$workspace"
  echo "hostfile=$hostfile"
  echo "np=$np"
  echo "mpi_lan_cidr=$mpi_lan_cidr"
  echo "results_dir=$results_dir"
  echo
  echo "HOSTFILE_CONTENT"
  cat "$hostfile"
  echo
  echo "COMMAND: mpirun --hostfile $hostfile --map-by node -np $np ${mpi_common[*]} ./parallel_unit_tests 1000000 12 8 300000"
  mpirun --hostfile "$hostfile" --map-by node -np "$np" "${mpi_common[@]}" \
    ./parallel_unit_tests 1000000 12 8 300000
  echo
  echo "LOG_FILE=$log_file"
} | tee "$log_file"

ln -sfn "$results_dir" "$workspace/results/latest"
echo "LATEST_RESULTS=$workspace/results/latest"
