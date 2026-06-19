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

echo "HOSTS_AND_KEYS_READY=YES"
getent hosts master node1 node2 || true

