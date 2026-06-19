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

CLUSTER_USER="${CLUSTER_USER:-$(id -un)}"
MASTER_USER="${MASTER_USER:-$CLUSTER_USER}"
NODE1_USER="${NODE1_USER:-$CLUSTER_USER}"
NODE2_USER="${NODE2_USER:-$CLUSTER_USER}"

for var in MASTER_IP NODE1_IP NODE2_IP MASTER_PUBLIC_KEY NODE1_PUBLIC_KEY NODE2_PUBLIC_KEY; do
  if [[ -z "${!var:-}" || "${!var}" == *REPLACE_WITH* ]]; then
    echo "Please set $var in $env_file" >&2
    exit 1
  fi
done

tmp_hosts="$(mktemp)"
awk '
  /# BEGIN parallel-macbook-cluster-setup/ {skip=1; next}
  /# END parallel-macbook-cluster-setup/ {skip=0; next}
  skip != 1 {print}
' /etc/hosts > "$tmp_hosts"

{
  echo "# BEGIN parallel-macbook-cluster-setup"
  echo "$MASTER_IP master"
  echo "$NODE1_IP node1"
  echo "$NODE2_IP node2"
  echo "# END parallel-macbook-cluster-setup"
} >> "$tmp_hosts"

sudo cp "$tmp_hosts" /etc/hosts
rm -f "$tmp_hosts"

install -d -m 700 "$HOME/.ssh"
touch "$HOME/.ssh/authorized_keys"
chmod 600 "$HOME/.ssh/authorized_keys"

for key in "$MASTER_PUBLIC_KEY" "$NODE1_PUBLIC_KEY" "$NODE2_PUBLIC_KEY"; do
  grep -qxF "$key" "$HOME/.ssh/authorized_keys" || echo "$key" >> "$HOME/.ssh/authorized_keys"
done

chmod 600 "$HOME/.ssh/authorized_keys"

ssh_config="$HOME/.ssh/config"
touch "$ssh_config"
chmod 600 "$ssh_config"

tmp_config="$(mktemp)"
awk '
  /# BEGIN parallel-macbook-cluster-setup/ {skip=1; next}
  /# END parallel-macbook-cluster-setup/ {skip=0; next}
  skip != 1 {print}
' "$ssh_config" > "$tmp_config"

{
  echo "# BEGIN parallel-macbook-cluster-setup"
  echo "Host master"
  echo "  HostName $MASTER_IP"
  echo "  User $MASTER_USER"
  echo "  StrictHostKeyChecking accept-new"
  echo "Host node1"
  echo "  HostName $NODE1_IP"
  echo "  User $NODE1_USER"
  echo "  StrictHostKeyChecking accept-new"
  echo "Host node2"
  echo "  HostName $NODE2_IP"
  echo "  User $NODE2_USER"
  echo "  StrictHostKeyChecking accept-new"
  echo "# END parallel-macbook-cluster-setup"
} >> "$tmp_config"

mv "$tmp_config" "$ssh_config"
chmod 600 "$ssh_config"

echo "HOSTS_AND_KEYS_READY=YES"
getent hosts master node1 node2 || true
