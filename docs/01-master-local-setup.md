# 01 - Master Local Setup

Chạy trên Ubuntu VM của máy master.

## 1. Bootstrap base

```bash
cd ~/parallel-macbook-cluster-setup
sudo bash scripts/common_root_bootstrap.sh master
```

Script sẽ:

- cài OpenMPI, compiler, SSH, NFS package;
- đặt hostname thành `master`;
- tạo `/shared/mpi`;
- tạo SSH key `~/.ssh/id_ed25519` nếu chưa có.

## 2. Chuẩn bị MPI samples

```bash
cd ~/parallel-macbook-cluster-setup
bash scripts/master_prepare_shared_mpi.sh
```

## 3. Test local trên master

```bash
bash scripts/run_local_smoke.sh
```

Pass khi:

```text
hello: có rank 0/2 và 1/2
ring: token quay về rank 0
reduce_sum: Correct? YES
pingpong: có average_round_trip_us
```

## 4. Lấy thông tin gửi nhóm

```bash
bash scripts/collect_node_info.sh
```

Gửi cho nhóm:

```text
role: master
IP: <IPv4 LAN sau khi Bridged>
public key: <ssh-ed25519 ...>
```

