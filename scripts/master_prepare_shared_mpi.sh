#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
shared="/shared/mpi"
owner="$(id -un)"

sudo mkdir -p "$shared"
sudo cp "$repo_root"/mpi_samples/*.c "$shared"/
sudo cp "$repo_root/configs/hosts.template" "$shared"/hosts.template
sudo cp "$repo_root/README.md" "$shared"/README_CLUSTER_SETUP.md
sudo chown -R "$owner:$owner" /shared
sudo chmod 775 /shared "$shared"

cd "$shared"
mpicc hello.c -o hello
mpicc ring.c -o ring
mpicc reduce_sum.c -o reduce_sum
mpicc pingpong.c -o pingpong

echo "MASTER_SHARED_MPI_READY=YES"
echo "workspace=$shared"
ls -la "$shared"

