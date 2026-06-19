# 02 - Worker Setup

Chạy trên Ubuntu VM của node1 và node2.

## 1. Bootstrap base

Node1:

```bash
cd ~/parallel-macbook-cluster-setup
sudo bash scripts/common_root_bootstrap.sh node1
```

Node2:

```bash
cd ~/parallel-macbook-cluster-setup
sudo bash scripts/common_root_bootstrap.sh node2
```

## 2. Lấy thông tin gửi master

```bash
bash scripts/collect_node_info.sh
```

Gửi cho master:

```text
role: node1 hoặc node2
IP: <IPv4 LAN sau khi Bridged>
public key: <ssh-ed25519 ...>
```

## 3. Sau khi master gửi lại cluster.env

Đặt file `configs/cluster.env` giống nhau trên cả 3 VM, rồi chạy:

```bash
bash scripts/write_cluster_hosts_and_keys.sh
```

Sau khi master bật NFS, chạy trên worker:

```bash
bash scripts/worker_mount_nfs.sh
ls -la /shared/mpi
```

