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

if [[ -z "${LAN_SUBNET:-}" ]]; then
  IFS=. read -r a b c _ <<< "$MASTER_IP"
  LAN_SUBNET="$a.$b.$c.0/24"
fi

sudo mkdir -p /shared/mpi
sudo chown -R "$(id -un):$(id -gn)" /shared
sudo chmod 775 /shared /shared/mpi

sudo cp /etc/exports "/etc/exports.bak.$(date +%Y%m%d%H%M%S)"
sudo sed -i '/# parallel-macbook-cluster-setup$/d' /etc/exports
echo "/shared/mpi $LAN_SUBNET(rw,sync,no_subtree_check) # parallel-macbook-cluster-setup" \
  | sudo tee -a /etc/exports >/dev/null

sudo exportfs -a
sudo systemctl restart nfs-kernel-server
sudo exportfs -v

echo "MASTER_NFS_READY=YES"
echo "export=/shared/mpi $LAN_SUBNET"

