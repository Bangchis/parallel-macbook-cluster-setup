#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "FULL_MASTER_LOCAL_SETUP"
echo "repo=$repo_root"
echo
echo "Step 1/3: root bootstrap. You may be asked for the Ubuntu sudo password."
sudo bash "$repo_root/scripts/common_root_bootstrap.sh" master
echo
echo "Step 2/3: prepare /shared/mpi"
bash "$repo_root/scripts/master_prepare_shared_mpi.sh"
echo
echo "Step 3/3: run local OpenMPI smoke"
bash "$repo_root/scripts/run_local_smoke.sh" /shared/mpi
echo
echo "MASTER_LOCAL_SETUP_DONE=YES"
echo "Next, send this node info to teammates:"
bash "$repo_root/scripts/collect_node_info.sh"

