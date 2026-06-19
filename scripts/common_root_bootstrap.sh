#!/usr/bin/env bash
set -euo pipefail

ROLE="${1:-}"
CLUSTER_USER="${CLUSTER_USER:-${SUDO_USER:-mpot}}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run with sudo: sudo bash scripts/common_root_bootstrap.sh <master|node1|node2>" >&2
  exit 1
fi

case "$ROLE" in
  master|node1|node2) ;;
  *)
    echo "Usage: sudo bash scripts/common_root_bootstrap.sh <master|node1|node2>" >&2
    exit 1
    ;;
esac

if ! id "$CLUSTER_USER" >/dev/null 2>&1; then
  echo "User $CLUSTER_USER does not exist" >&2
  exit 1
fi

apt update
apt install -y \
  build-essential \
  openmpi-bin \
  libopenmpi-dev \
  python3-mpi4py \
  openssh-server \
  openssh-client \
  nfs-kernel-server \
  nfs-common \
  net-tools \
  htop \
  git \
  curl \
  nano

hostnamectl set-hostname "$ROLE"
systemctl enable --now ssh

mkdir -p /shared/mpi
chown -R "$CLUSTER_USER:$CLUSTER_USER" /shared
chmod 775 /shared /shared/mpi

install -d -m 700 -o "$CLUSTER_USER" -g "$CLUSTER_USER" "/home/$CLUSTER_USER/.ssh"
touch "/home/$CLUSTER_USER/.ssh/authorized_keys"
chown "$CLUSTER_USER:$CLUSTER_USER" "/home/$CLUSTER_USER/.ssh/authorized_keys"
chmod 600 "/home/$CLUSTER_USER/.ssh/authorized_keys"

if [[ ! -f "/home/$CLUSTER_USER/.ssh/id_ed25519" ]]; then
  sudo -u "$CLUSTER_USER" ssh-keygen -t ed25519 -C "parallel-cluster-$ROLE" \
    -f "/home/$CLUSTER_USER/.ssh/id_ed25519" -N ""
fi

echo "BOOTSTRAP_DONE=YES"
echo "role=$ROLE"
echo "hostname=$(hostname)"
echo "ip=$(hostname -I)"
echo "public_key=$(cat "/home/$CLUSTER_USER/.ssh/id_ed25519.pub")"
