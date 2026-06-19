# Parallel MacBook Cluster Setup

Repo này dùng để kết nối 3 MacBook thành một cụm Ubuntu VM chạy SSH, NFS và
OpenMPI cho môn Parallel Programming / Parallel Computing.

Repo này không phụ thuộc vào MPOT. Dự án cuối kì thật sự sẽ đặt sau; hiện tại
mục tiêu chỉ là dựng hạ tầng cluster trước.

## Mô hình

```text
MacBook 1 -> Ubuntu VM master -> hostname master -> user mpiuser
MacBook 2 -> Ubuntu VM node1  -> hostname node1  -> user mpiuser
MacBook 3 -> Ubuntu VM node2  -> hostname node2  -> user mpiuser
```

Mỗi MacBook chạy đúng một Ubuntu ARM64 VM. Không dùng cloud, Docker hay
VirtualBox cho cụm cuối kì.

Master cũng là compute node: nếu hostfile có `master slots=...`, OpenMPI sẽ
chạy rank trên master cùng node1/node2.

## Luồng làm việc

0. Mỗi MacBook tạo hoặc mở đúng một Ubuntu ARM64 VM trong UTM. Xem thêm
`docs/00-utm-bridged-network.md`.

1. Trên từng VM, copy hoặc clone repo này vào home:

```bash
cd ~
git clone <repo-url> parallel-macbook-cluster-setup
```

Nếu chưa có GitHub repo, có thể copy từ macOS bằng `rsync`.

2. Trên từng VM, chạy bootstrap base:

```bash
cd ~/parallel-macbook-cluster-setup
sudo bash scripts/common_root_bootstrap.sh master
```

Trên worker đổi `master` thành `node1` hoặc `node2`.

3. Trên master, chuẩn bị thư mục test OpenMPI:

```bash
cd ~/parallel-macbook-cluster-setup
bash scripts/master_prepare_shared_mpi.sh
bash scripts/run_local_smoke.sh
```

4. Khi cả 3 VM đã chạy local xong, chuyển network VM sang Bridged, rồi mỗi VM
lấy thông tin:

```bash
bash scripts/collect_node_info.sh
```

5. Điền IP và SSH public key vào `configs/cluster.env` từ file mẫu:

```bash
cp configs/cluster.env.example configs/cluster.env
nano configs/cluster.env
```

6. Trên cả 3 VM, cập nhật hostname và key:

```bash
bash scripts/write_cluster_hosts_and_keys.sh
```

7. Trên master, bật NFS export:

```bash
bash scripts/master_configure_nfs.sh
```

8. Trên node1 và node2, mount thư mục master:

```bash
bash scripts/worker_mount_nfs.sh
```

9. Trên master, chạy test cluster:

```bash
cd /shared/mpi
cp hosts.template hosts
bash ~/parallel-macbook-cluster-setup/scripts/run_cluster_smoke.sh
```

Pass khi `hello`, `ring`, `reduce_sum`, `pingpong` chạy qua hostfile và log có
rank từ nhiều hostname.

## Các file quan trọng

- `configs/cluster.env.example`: template IP/key của 3 VM.
- `mpi_samples/`: code C/MPI độc lập để test cluster.
- `scripts/common_root_bootstrap.sh`: cài package base trên từng VM.
- `scripts/master_prepare_shared_mpi.sh`: tạo `/shared/mpi` trên master.
- `scripts/write_cluster_hosts_and_keys.sh`: cập nhật `/etc/hosts` và SSH key.
- `scripts/master_configure_nfs.sh`: export `/shared/mpi` từ master.
- `scripts/worker_mount_nfs.sh`: mount `/shared/mpi` trên worker.
- `scripts/reconnect_after_lan_change.sh`: cập nhật IP và reconnect khi đổi
  Wi-Fi/LAN.
- `docs/`: hướng dẫn từng giai đoạn.

Khi đổi sang mạng LAN khác và IP thay đổi, xem
`docs/05-lan-change-reconnect.md`.

Khi chia sẻ repo cho bạn trong nhóm hoặc thay zip bằng GitHub, xem
`docs/06-github-team-workflow.md`.

Khi muốn chạy các bài unit test MPI có in/lưu kết quả để demo, xem
`docs/07-running-parallel-tests.md`.

Repo co ca unit test C/OpenMPI va Python/mpi4py. Python test nam trong
`python_tests/` va chay bang `scripts/run_python_parallel_tests.sh`.

## Trạng thái mong muốn trước khi làm project thật

```text
master ping node1/node2 OK
master ssh node1/node2 không hỏi password
node1/node2 mount được master:/shared/mpi
mpirun --hostfile hosts chạy được trên cả 3 VM
```
