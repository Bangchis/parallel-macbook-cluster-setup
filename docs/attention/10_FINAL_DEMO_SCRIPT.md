# Final Demo Script

Use this as the live demo checklist.

## 1. Show The Cluster

On the master VM:

```bash
cd ~/parallel-macbook-cluster-setup
mpirun -np 3 --hostfile configs/hosts hostname
```

Expected output includes:

```text
master
node1
node2
```

What to say:

- The cluster uses 3 physical MacBooks.
- Each physical machine runs one Ubuntu VM.
- OpenMPI launches ranks through SSH.
- The master is also a compute node, not only a coordinator.

## 2. Show Correctness

```bash
bash scripts/run_demo_correctness.sh
```

Expected:

```text
CORRECTNESS_PASS=YES
max_abs_error=...
relative_l2_error=...
```

What to say:

- Parallel output is compared with serial row-wise attention.
- The accepted error is small because all implementations compute the same
  self-attention formula.

## 3. Show Ranks Computing

After running the final pipeline, open:

```text
results/final_.../raw/rank_metrics.csv
```

Show these columns:

```text
rank,hostname,rows_assigned,compute_ms,bcast_ms,gather_ms,reduce_ms
```

What to say:

- Each hostname has assigned rows.
- `rows_assigned > 0` means the machine computed output rows.
- `compute_ms` and communication columns are measured separately.

## 4. Show Required Experiments

Open:

```text
results/final_.../figures/
```

Show in this order:

1. `01_runtime_vs_L.png`
2. `03_speedup.png`
3. `04_efficiency.png`
4. `05_rank_breakdown.png`
5. `06_granularity_load_balance.png`
6. `07_memory_comparison.png`
7. `10_comm_strategy.png`
8. `11_thread_scaling.png`

What to say:

- Runtime grows near `L^2`.
- Speedup improves but is limited by communication and synchronization.
- Load balance is controlled by row-block granularity `Br`.
- Online softmax reduces memory compared with full attention.
- Non-blocking MPI is included as a communication-strategy comparison.
- Thread scaling shows the OpenMP part of the hybrid implementation.

## 5. Show Readiness Report

Open:

```text
results/final_.../readiness.md
```

Expected:

```text
FINAL_READINESS_STATUS=PASS
```

If there are warnings:

- Explain whether they are local-smoke warnings or real missing final data.
- For final submission, cluster hostnames should include `master`, `node1`,
  and `node2`.

## 6. Short Explanation If Asked For Pseudocode

```text
rank 0 generates Q, K, V
MPI broadcasts Q, K, V to all ranks
each rank maps query rows using block-cyclic assignment
OpenMP threads compute local rows with blocked online softmax
MPI reduces output and checksum to rank 0
rank 0 compares with serial baseline and writes metrics
```
