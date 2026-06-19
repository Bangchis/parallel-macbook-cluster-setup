#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="${1:-$repo_root/configs/cluster.env}"

if [[ ! -f "$env_file" ]]; then
  echo "Missing $env_file. Copy configs/cluster.env.example to configs/cluster.env first." >&2
  exit 1
fi

# shellcheck disable=SC1090
source "$env_file"

sudo mkdir -p /shared/mpi
if ! mountpoint -q /shared/mpi; then
  sudo mount master:/shared/mpi /shared/mpi
fi

fstab_line="master:/shared/mpi /shared/mpi nfs defaults,_netdev 0 0"
if ! grep -qxF "$fstab_line" /etc/fstab; then
  echo "$fstab_line" | sudo tee -a /etc/fstab >/dev/null
fi

echo "WORKER_NFS_MOUNT_READY=YES"
mount | grep '/shared/mpi' || true
ls -la /shared/mpi
