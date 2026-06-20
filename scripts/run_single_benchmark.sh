#!/usr/bin/env bash
set -euo pipefail

bash scripts/build.sh

np="${ATTN_NP:-3}"
hostfile="${ATTN_HOSTFILE:-configs/hosts}"
use_hostfile="${ATTN_USE_HOSTFILE:-1}"
algo="${ATTN_ALGO:-mpi_online}"
B="${ATTN_B:-1}"
H="${ATTN_H:-2}"
L="${ATTN_L:-128}"
Dh="${ATTN_DH:-32}"
Br="${ATTN_BR:-16}"
Bc="${ATTN_BC:-64}"
causal="${ATTN_CAUSAL:-0}"
assignment="${ATTN_ASSIGNMENT:-block_cyclic}"
schedule="${ATTN_SCHEDULE:-static}"
threads="${ATTN_THREADS:-2}"
repeat="${ATTN_REPEAT:-1}"
verify="${ATTN_VERIFY:-1}"
run_id="${ATTN_RUN_ID:-single}"
output="${ATTN_OUTPUT:-results/raw/summary.csv}"

cmd=(./build/attention_bench
  --algo "$algo"
  --B "$B" --H "$H" --L "$L" --Dh "$Dh"
  --Br "$Br" --Bc "$Bc"
  --causal "$causal"
  --assignment "$assignment"
  --schedule "$schedule"
  --omp_threads "$threads"
  --repeat "$repeat"
  --verify "$verify"
  --debug "${ATTN_DEBUG:-0}"
  --run_id "$run_id"
  --output "$output")

if [[ "$algo" == mpi_* && "$np" -gt 1 ]]; then
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
  echo "COMMAND: ${mpi[*]} ${cmd[*]}"
  "${mpi[@]}" "${cmd[@]}"
else
  export OMPI_MCA_btl="${OMPI_MCA_btl:-self}"
  echo "COMMAND: ${cmd[*]}"
  "${cmd[@]}"
fi
