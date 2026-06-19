#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
workspace="${1:-/shared/mpi}"

if [[ ! -d "$workspace" ]]; then
  workspace="$repo_root/mpi_samples"
fi

cd "$workspace"

mpicc hello.c -o hello
mpicc ring.c -o ring
mpicc reduce_sum.c -o reduce_sum
mpicc pingpong.c -o pingpong

{
  echo "LOCAL_OPENMPI_SMOKE"
  date -Is
  echo "hostname=$(hostname)"
  echo "ips=$(hostname -I)"
  echo "workspace=$workspace"
  echo
  echo "COMMAND: mpirun -np 2 ./hello"
  mpirun -np 2 ./hello
  echo
  echo "COMMAND: mpirun -np 2 ./ring"
  mpirun -np 2 ./ring
  echo
  echo "COMMAND: mpirun -np 2 ./reduce_sum 1000000"
  mpirun -np 2 ./reduce_sum 1000000
  echo
  echo "COMMAND: mpirun -np 2 ./pingpong"
  mpirun -np 2 ./pingpong
} | tee "$workspace/local_smoke_log.txt"
