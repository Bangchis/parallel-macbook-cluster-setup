#!/usr/bin/env bash
set -euo pipefail

workspace="${1:-/shared/mpi}"
hostfile="${2:-$workspace/hosts}"
mpi_lan_cidr="${MPI_LAN_CIDR:-${LAN_SUBNET:-192.168.31.0/24}}"
mpi_common=(
  --mca btl tcp,self
  --mca btl_tcp_if_include "$mpi_lan_cidr"
  --mca btl_tcp_disable_family 6
)

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
  echo "mpi_lan_cidr=$mpi_lan_cidr"
  echo
  echo "COMMAND: mpirun --hostfile $hostfile ${mpi_common[*]} -np 3 ./hello"
  mpirun --hostfile "$hostfile" "${mpi_common[@]}" -np 3 ./hello
  echo
  echo "COMMAND: mpirun --hostfile $hostfile ${mpi_common[*]} -np 6 ./ring"
  mpirun --hostfile "$hostfile" "${mpi_common[@]}" -np 6 ./ring
  echo
  echo "COMMAND: mpirun --hostfile $hostfile ${mpi_common[*]} -np 6 ./reduce_sum 100000000"
  mpirun --hostfile "$hostfile" "${mpi_common[@]}" -np 6 ./reduce_sum 100000000
  echo
  echo "COMMAND: mpirun --hostfile $hostfile ${mpi_common[*]} -np 2 ./pingpong"
  mpirun --hostfile "$hostfile" "${mpi_common[@]}" -np 2 ./pingpong
  echo
  echo "CLUSTER_READY_FOR_DEMO=YES"
} | tee "$workspace/final_cluster_test_log.txt"
