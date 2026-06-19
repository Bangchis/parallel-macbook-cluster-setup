#!/usr/bin/env bash
set -euo pipefail

echo "NODE_INFO"
echo "hostname=$(hostname)"
echo "ips=$(hostname -I)"
echo "arch=$(uname -m)"
echo "ubuntu=$(lsb_release -ds 2>/dev/null || cat /etc/os-release)"
echo "user=$(id -un)"
echo "mpicc=$(command -v mpicc || true)"
echo "mpirun=$(command -v mpirun || true)"
echo "ssh_status=$(systemctl is-active ssh 2>/dev/null || true)"

if [[ -f "$HOME/.ssh/id_ed25519.pub" ]]; then
  echo "public_key=$(cat "$HOME/.ssh/id_ed25519.pub")"
else
  echo "public_key=MISSING"
fi

