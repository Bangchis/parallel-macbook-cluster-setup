#!/usr/bin/env bash
set -euo pipefail

script_path="${BASH_SOURCE[0]}"
if command -v readlink >/dev/null 2>&1; then
  resolved_path="$(readlink -f "$script_path" 2>/dev/null || true)"
  if [[ -n "$resolved_path" ]]; then
    script_path="$resolved_path"
  fi
fi
repo_root="$(cd "$(dirname "$script_path")/.." && pwd)"

echo "FULL_MASTER_LOCAL_SETUP"
echo "repo=$repo_root"

if [[ "${1:-}" == "--path-check" ]]; then
  test -f "$repo_root/scripts/common_root_bootstrap.sh"
  test -f "$repo_root/scripts/master_prepare_shared_mpi.sh"
  test -f "$repo_root/scripts/run_local_smoke.sh"
  echo "PATH_CHECK_OK=YES"
  exit 0
fi

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
