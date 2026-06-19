# 03 - LAN Finalize

Chỉ làm bước này sau khi cả 3 VM đã bootstrap xong và đã chuyển network sang
Bridged.

## 1. Điền configs/cluster.env

Trên master:

```bash
cd ~/parallel-macbook-cluster-setup
cp configs/cluster.env.example configs/cluster.env
nano configs/cluster.env
```

Điền IP và public key của cả 3 VM.

Copy file `configs/cluster.env` sang node1 và node2.

## 2. Cập nhật hosts và authorized_keys

Chạy trên cả 3 VM:

```bash
cd ~/parallel-macbook-cluster-setup
bash scripts/write_cluster_hosts_and_keys.sh
```

## 3. Test ping và SSH từ master

```bash
ping -c 3 node1
ping -c 3 node2
ssh mpot@node1 hostname
ssh mpot@node2 hostname
```

Nếu SSH còn hỏi password, kiểm tra lại public key trong `configs/cluster.env`.

## 4. Bật NFS trên master

```bash
cd ~/parallel-macbook-cluster-setup
bash scripts/master_configure_nfs.sh
```

## 5. Mount NFS trên worker

Trên node1 và node2:

```bash
cd ~/parallel-macbook-cluster-setup
bash scripts/worker_mount_nfs.sh
```

## 6. Chạy OpenMPI cluster smoke từ master

```bash
cd /shared/mpi
cp hosts.template hosts
bash ~/parallel-macbook-cluster-setup/scripts/run_cluster_smoke.sh
```

Kết quả được lưu ở:

```text
/shared/mpi/final_cluster_test_log.txt
```

