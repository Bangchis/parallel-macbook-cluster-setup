#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
workspace="${1:-/shared/mpi}"
hostfile="${2:-$workspace/hosts_all_1slot}"
np="${MPI_TEST_NP:-3}"
mpi_lan_cidr="${MPI_LAN_CIDR:-${LAN_SUBNET:-192.168.31.0/24}}"
timestamp="$(date +%Y%m%d-%H%M%S)"
results_dir="${RESULTS_DIR:-$workspace/results/$timestamp-python-parallel-tests}"
log_file="$results_dir/python_parallel_tests.log"

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

if ! python3 -c 'import mpi4py' >/dev/null 2>&1; then
  echo "Missing mpi4py on master. Run: bash scripts/install_python_mpi_deps.sh" >&2
  exit 1
fi

mkdir -p "$workspace" "$results_dir"
cp "$repo_root/python_tests/parallel_unit_tests.py" "$workspace/python_parallel_unit_tests.py"

cd "$workspace"

{
  echo "PYTHON_PARALLEL_UNIT_TEST_RUN"
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
  echo "COMMAND: mpirun --hostfile $hostfile --map-by node -np $np ${mpi_common[*]} python3 -c 'from mpi4py import MPI; print(...)'"
  mpirun --hostfile "$hostfile" --map-by node -np "$np" "${mpi_common[@]}" \
    python3 -c 'from mpi4py import MPI; print(f"mpi4py_preflight rank={MPI.COMM_WORLD.Get_rank()} host={MPI.Get_processor_name()}", flush=True)'
  echo
  echo "COMMAND: mpirun --hostfile $hostfile --map-by node -np $np ${mpi_common[*]} python3 python_parallel_unit_tests.py"
  mpirun --hostfile "$hostfile" --map-by node -np "$np" "${mpi_common[@]}" \
    python3 python_parallel_unit_tests.py
  echo
  echo "LOG_FILE=$log_file"
} | tee "$log_file"

ln -sfn "$results_dir" "$workspace/results/latest-python"
echo "LATEST_PYTHON_RESULTS=$workspace/results/latest-python"
