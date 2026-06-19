#!/usr/bin/env bash
set -euo pipefail

workspace="${1:-/shared/mpi}"
hostfile="${2:-$workspace/hosts}"

cd "$workspace"

if [[ ! -f "$hostfile" ]]; then
  echo "Missing hostfile: $hostfile" >&2
  echo "Create it from hosts.template after LAN hostnames work." >&2
  exit 1
fi

mpicc hello.c -o hello
mpicc ring.c -o ring
mpicc reduce_sum.c -o reduce_sum
mpicc pingpong.c -o pingpong

{
  echo "CLUSTER_OPENMPI_SMOKE"
  date -Is
  echo "hostname=$(hostname)"
  echo "ips=$(hostname -I)"
  echo "workspace=$workspace"
  echo "hostfile=$hostfile"
  echo
  echo "COMMAND: mpirun --hostfile $hostfile -np 3 ./hello"
  mpirun --hostfile "$hostfile" -np 3 ./hello
  echo
  echo "COMMAND: mpirun --hostfile $hostfile -np 6 ./ring"
  mpirun --hostfile "$hostfile" -np 6 ./ring
  echo
  echo "COMMAND: mpirun --hostfile $hostfile -np 6 ./reduce_sum 100000000"
  mpirun --hostfile "$hostfile" -np 6 ./reduce_sum 100000000
  echo
  echo "COMMAND: mpirun --hostfile $hostfile -np 2 ./pingpong"
  mpirun --hostfile "$hostfile" -np 2 ./pingpong
  echo
  echo "CLUSTER_READY_FOR_DEMO=YES"
} | tee "$workspace/final_cluster_test_log.txt"

