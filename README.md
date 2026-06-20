# Parallel MacBook Cluster Setup

Repo này dùng để kết nối 3 MacBook thành một cụm Ubuntu VM chạy SSH, NFS và
OpenMPI cho môn Parallel Programming / Parallel Computing.

Repo này không phụ thuộc vào MPOT. Ngoài phần cluster setup, repo đã có project
cuối kì:

```text
Hybrid MPI + OpenMP Blocked Online Self-Attention
```

Project chỉ tính self-attention inference kernel:

```text
O = softmax(QK^T / sqrt(Dh)) V
```

Không train Transformer, không dùng GPU, không dùng PyTorch/CUDA.

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

## Self-Attention Project

Build:

```bash
bash scripts/build.sh
```

Correctness tests:

```bash
bash scripts/run_unit_tests.sh
```

Demo correctness tren cluster:

```bash
bash scripts/run_demo_correctness.sh
```

One-command final demo on the cluster:

```bash
bash scripts/run_final_demo.sh
```

If the other machines are not on the same LAN, run a local-only demo smoke:

```bash
ATTN_USE_HOSTFILE=0 ATTN_DEMO_NP=2 bash scripts/run_final_demo.sh
```

The demo writes `results/demo_YYYYMMDD-HHMMSS/demo_terminal.log` and
`results/demo_YYYYMMDD-HHMMSS/demo_summary.md`.

Demo performance:

```bash
bash scripts/run_demo_perf.sh
```

Communication strategy comparison:

```bash
bash scripts/run_comm_strategy_sweep.sh
```

Generate plots:

```bash
bash scripts/install_plot_deps.sh
.venv-plot/bin/python plots/plot_all.py --input results/raw --output results/figures
```

Generate report figures and tables:

```bash
bash scripts/run_report_artifacts.sh
```

This also generates `results/.../tables/analysis.md`, which summarizes the
main results for the report discussion, and
`results/.../report/final_report_draft.md`, which is a first report draft
assembled from the run artifacts. It also writes
`results/.../tables/experiment_advisor.md` with suggested next values for
`ATTN_FIND_N_LIST`, `ATTN_SELECTED_N`, `ATTN_ASSIGNMENT`, and `ATTN_BR`.

Run the full required final experiment pipeline on the cluster:

```bash
cp configs/attention_experiment.env.example configs/attention_experiment.env
nano configs/attention_experiment.env
python3 scripts/check_experiment_config.py --config configs/attention_experiment.env
bash scripts/run_required_experiments.sh
```

Run a tiny local smoke version of the final pipeline:

```bash
bash scripts/run_local_final_smoke.sh
```

Check final submission readiness:

```bash
python3 scripts/check_final_readiness.py --run-dir results/final_YYYYMMDD-HHMMSS --require-host master --require-host node1 --require-host node2
```

Cluster evidence is saved in:

```text
results/final_YYYYMMDD-HHMMSS/evidence/cluster_evidence.txt
```

The generated report draft is saved in:

```text
results/final_YYYYMMDD-HHMMSS/report/final_report_draft.md
```

Benchmark tuning advice is saved in:

```text
results/final_YYYYMMDD-HHMMSS/tables/experiment_advisor.md
results/final_YYYYMMDD-HHMMSS/tables/experiment_advisor.env
```

Member contribution evidence is saved in:

```text
results/final_YYYYMMDD-HHMMSS/tables/member_contributions.md
results/final_YYYYMMDD-HHMMSS/tables/member_contributions.csv
```

The raw speedup CSV is also post-processed so these columns are filled:

```text
speedup_with_comm
speedup_without_comm
efficiency_with_comm
efficiency_without_comm
```

Granularity/load-balance tables also include `idle_gap_pct`, computed from
per-rank idle time. The target is `<= 0.25`, matching the professor's 25%
idle-time rule.

Create a submission archive:

```bash
bash scripts/make_submission_package.sh --run-dir results/final_YYYYMMDD-HHMMSS
```

Docs chinh:

```text
docs/attention/00_PROJECT_OVERVIEW.md
docs/attention/01_ALGORITHM_EXPLANATION.md
docs/attention/02_MPI_OPENMP_DESIGN.md
docs/attention/03_DEMO_AND_BENCHMARK.md
docs/attention/04_MEMBER_TASKS.md
docs/attention/05_CODEBASE_GUIDE.md
docs/attention/06_VISUALIZATION_GUIDE.md
docs/attention/07_DEBUGGING_GUIDE.md
docs/attention/08_REPORT_OUTLINE.md
docs/attention/09_FINAL_EXPERIMENT_PIPELINE.md
docs/attention/10_FINAL_DEMO_SCRIPT.md
docs/attention/11_RUBRIC_MAPPING.md
report/FINAL_REPORT_TEMPLATE.md
```

## Trạng thái mong muốn trước khi làm project thật

```text
master ping node1/node2 OK
master ssh node1/node2 không hỏi password
node1/node2 mount được master:/shared/mpi
mpirun --hostfile hosts chạy được trên cả 3 VM
```
