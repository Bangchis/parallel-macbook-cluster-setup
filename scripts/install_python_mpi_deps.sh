#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -gt 0 ]]; then
  nodes=("$@")
else
  nodes=(master node1 node2)
fi

install_one() {
  local node="$1"
  echo
  echo "Installing Python MPI deps on $node ..."
  if [[ "$node" == "master" || "$node" == "$(hostname)" ]]; then
    sudo apt update
    sudo apt install -y python3-mpi4py
    python3 -c 'from mpi4py import MPI; print("mpi4py OK on", MPI.Get_processor_name())'
  else
    ssh -o BatchMode=yes -o ConnectTimeout=8 "$node" \
      'sudo apt update && sudo apt install -y python3-mpi4py && python3 -c "from mpi4py import MPI; print(\"mpi4py OK on\", MPI.Get_processor_name())"'
  fi
}

for node in "${nodes[@]}"; do
  install_one "$node"
done

echo
echo "PYTHON_MPI_DEPS_READY=YES"
