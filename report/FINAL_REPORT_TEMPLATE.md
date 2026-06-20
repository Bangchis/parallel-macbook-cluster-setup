# Hybrid MPI + OpenMP Blocked Online Self-Attention

Course: Parallel and Distributed Programming

Group members:

- Member 1:
- Member 2:
- Member 3:
- Member 4:

## 1. Introduction

This project implements the self-attention inference kernel:

```text
O = softmax(QK^T / sqrt(Dh)) V
```

The project does not train a Transformer. It focuses on parallelizing the
attention computation on a physical MPI cluster.

## 2. Cluster Setup

Cluster:

```text
master -> Ubuntu VM on MacBook 1
node1  -> Ubuntu VM on MacBook 2
node2  -> Ubuntu VM on MacBook 3
```

Each physical machine runs exactly one Ubuntu VM. Cloud machines are not used.

Insert evidence:

- `mpirun -np 3 --hostfile configs/hosts hostname`
- screenshot or terminal log showing `master`, `node1`, `node2`

## 3. Serial Algorithm

Input tensors:

```text
Q, K, V, O: B x H x L x Dh
```

For every query row `i`, the serial baseline computes:

1. scores `S[i, j] = dot(Q[i], K[j]) / sqrt(Dh)`
2. stable softmax using max subtraction
3. output `O[i] = sum_j softmax(S[i, j]) * V[j]`

Complexity:

```text
Time:   O(B * H * L^2 * Dh)
Memory: naive full attention stores O(B * H * L^2)
```

## 4. Blocked Online Softmax

The optimized version computes attention row by row and scans K/V in blocks.
It maintains:

```text
m = running maximum score
l = running softmax denominator
out = running weighted value vector
```

When a new block changes the maximum, the previous denominator and output are
rescaled before accumulating the new block.

This reduces memory because it does not materialize the full attention matrix.

## 5. Parallel Design

Parallel level:

- data-level parallelism over query rows
- hybrid MPI + OpenMP

Decomposition:

- 1D row decomposition over global query rows

Mapping:

- contiguous
- cyclic
- block-cyclic

Primary strategy:

```text
block_id = global_row / Br
owner_rank = block_id % world_size
```

Communication:

- blocking version: `MPI_Bcast`, `MPI_Reduce`, `MPI_Gather`
- non-blocking comparison: `MPI_Ibcast`, `MPI_Ireduce`

Load balancing:

```text
load_imbalance = max_rank_compute_ms / avg_rank_compute_ms
```

If load imbalance is greater than 1.25, the block granularity `Br` should be
adjusted.

## 6. Parallel Pseudocode

```text
rank 0 generates Q, K, V
MPI_Bcast Q, K, V to all ranks

for each rank r:
  OpenMP parallel for over global rows:
    if row belongs to rank r:
      compute blocked online attention row
      write local output row

MPI_Reduce local outputs into final output on rank 0
MPI_Reduce checksums
MPI_Gather rank metrics
MPI_Gather thread metrics

rank 0 compares final output with serial baseline
rank 0 writes CSV metrics
```

## 7. Correctness

Correctness is checked by comparing the parallel output with the serial
baseline.

Metrics:

- max absolute error
- mean absolute error
- relative L2 error

Insert table:

```text
results/final_.../tables/correctness.md
```

## 8. Experiments

Use:

```text
results/final_.../experiment_summary.env
results/final_.../tables/analysis.md
```

Report:

- selected `N`
- speedup input `2N`
- total number of physical CPU cores
- process list

### 8.1 Find N

Use total physical cores and sweep L until runtime is around 2-3 minutes.

Insert:

- `figures/01_runtime_vs_L.png`

### 8.2 Granularity And Load Balance

Use input size `N` and total physical cores.

Insert:

- `figures/05_rank_breakdown.png`
- `figures/06_granularity_load_balance.png`
- `tables/granularity.md`

### 8.3 Speedup

Use input size `2N` and process counts:

```text
1, 2, 4, 8, ..., total physical cores
```

Insert:

- `figures/02_runtime_with_without_comm.png`
- `figures/03_speedup.png`
- `figures/04_efficiency.png`
- `tables/speedup.md`

### 8.4 Memory

Compare full attention, row-wise attention, OpenMP online attention, and MPI
online attention.

Insert:

- `figures/07_memory_comparison.png`

### 8.5 Communication Strategy

Compare blocking and non-blocking MPI collectives.

Insert:

- `figures/10_comm_strategy.png`
- `tables/communication.md`

## 9. Discussion

Discuss:

- why runtime grows near `L^2`
- why communication overhead limits speedup
- whether block-cyclic mapping improves balance
- why online softmax reduces memory
- why master also computes rows

## 10. Member Contributions

Member 1:

- tensor/config/serial/correctness

Member 2:

- online softmax/OpenMP/metrics

Member 3:

- MPI implementation/communication/rank metrics

Member 4:

- scripts/plots/report artifacts/docs

## 11. Conclusion

Summarize:

- cluster setup was successful
- parallel output matches serial baseline
- speedup and efficiency were measured
- load balancing was analyzed
- future work: 2D decomposition, better overlap, GPU comparison
