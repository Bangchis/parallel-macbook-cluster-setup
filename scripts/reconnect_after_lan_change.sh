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
SLOTS_PER_NODE="${SLOTS_PER_NODE:-4}"

for var in MASTER_IP NODE1_IP NODE2_IP; do
  if [[ -z "${!var:-}" || "${!var}" == *REPLACE_WITH* ]]; then
    echo "Please set $var in $env_file" >&2
    exit 1
  fi
done

if [[ -z "${LAN_SUBNET:-}" ]]; then
  IFS=. read -r a b c _ <<< "$MASTER_IP"
  LAN_SUBNET="$a.$b.$c.0/24"
fi

echo "RECONNECT_CLUSTER_AFTER_LAN_CHANGE"
echo "env_file=$env_file"
echo "master=$MASTER_IP user=$MASTER_USER"
echo "node1=$NODE1_IP user=$NODE1_USER"
echo "node2=$NODE2_IP user=$NODE2_USER"
echo "lan_subnet=$LAN_SUBNET"
echo

"$repo_root/scripts/write_cluster_hosts_and_keys.sh" "$env_file"
"$repo_root/scripts/master_configure_nfs.sh" "$env_file"

sudo mkdir -p /shared/mpi
sudo chown -R "$(id -un):$(id -gn)" /shared

cat > /shared/mpi/hosts <<HOSTS
master slots=$SLOTS_PER_NODE
node1 slots=$SLOTS_PER_NODE
node2 slots=$SLOTS_PER_NODE
HOSTS

cat > /shared/mpi/hosts_all_1slot <<'HOSTS'
master slots=1
node1 slots=1
node2 slots=1
HOSTS

cat > /shared/mpi/hosts_master_node1_1slot <<'HOSTS'
master slots=1
node1 slots=1
HOSTS

cat > /shared/mpi/hosts_master_node2_1slot <<'HOSTS'
master slots=1
node2 slots=1
HOSTS

cd /shared/mpi
mpicc hello.c -o hello

remote_refresh_node() {
  local node="$1"
  local user="$2"
  local ip="$3"

  echo
  echo "Refreshing $node at $ip ..."
  ssh -o BatchMode=yes -o ConnectTimeout=8 "$node" hostname
  ssh "$node" sudo bash -s -- "$MASTER_IP" "$NODE1_IP" "$NODE2_IP" <<'REMOTE'
set -euo pipefail
master_ip="$1"
node1_ip="$2"
node2_ip="$3"

tmp_hosts="$(mktemp)"
awk '
  /# BEGIN parallel-macbook-cluster-setup/ {skip=1; next}
  /# END parallel-macbook-cluster-setup/ {skip=0; next}
  skip != 1 {print}
' /etc/hosts > "$tmp_hosts"

{
  echo "# BEGIN parallel-macbook-cluster-setup"
  echo "$master_ip master"
  echo "$node1_ip node1"
  echo "$node2_ip node2"
  echo "# END parallel-macbook-cluster-setup"
} >> "$tmp_hosts"

cp "$tmp_hosts" /etc/hosts
rm -f "$tmp_hosts"

mkdir -p /shared/mpi
if mountpoint -q /shared/mpi; then
  umount /shared/mpi || umount -lf /shared/mpi || true
fi
mount -t nfs "${master_ip}:/shared/mpi" /shared/mpi
mount | grep '/shared/mpi'
getent hosts master node1 node2
REMOTE

  ssh "$node" "test -x /shared/mpi/hello && echo ${node}_SHARED_MPI_OK"
}

remote_refresh_node node1 "$NODE1_USER" "$NODE1_IP"
remote_refresh_node node2 "$NODE2_USER" "$NODE2_IP"

echo
echo "Running 3-node hello smoke..."
mpirun --hostfile hosts_all_1slot --map-by node -np 3 \
  --mca btl tcp,self \
  --mca btl_tcp_if_include "$LAN_SUBNET" \
  --mca btl_tcp_disable_family 6 \
  ./hello

echo
echo "RECONNECT_READY=YES"
