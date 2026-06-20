# MPI + OpenMP Design

Parallel level:

- Data-level parallelism over query rows.
- Hybrid MPI + OpenMP.

Global row:

```text
global_row = ((b * H + h) * L + i)
```

## Mapping

`contiguous`:

```text
rank 0: first block of rows
rank 1: next block
...
```

`cyclic`:

```text
row belongs to rank if global_row % world_size == rank
```

`block_cyclic`:

```text
block_id = global_row / Br
row belongs to rank if block_id % world_size == rank
```

`block_cyclic` la strategy chinh cho report vi no cho phep dieu chinh
granularity bang `Br`.

## Communication

Current implementation:

1. rank 0 tao Q/K/V.
2. `MPI_Bcast` Q/K/V den all ranks.
3. moi rank compute assigned rows.
4. `MPI_Reduce` output ve rank 0.
5. `MPI_Reduce` checksum.
6. `MPI_Gather` rank metrics va thread metrics.

Blocking communication duoc dung de code don gian va de giai thich.

Experimental non-blocking implementation:

- `mpi_online_nb`
- `mpi_row_nb`

This version uses:

- `MPI_Ibcast` for Q/K/V.
- `MPI_Ireduce` for output and checksum.

The main report can use blocking MPI as the primary design and use the
non-blocking version as an ablation to discuss communication strategy.

## Load Balancing

```text
load_imbalance = max_rank_compute_ms / avg_rank_compute_ms
idle_gap_pct = (max_idle_ms - min_idle_ms) / max_rank_compute_ms
```

Neu `load_imbalance > 1.25` hoac `idle_gap_pct > 0.25`, report can thu `Br`
nho hon/lon hon va so sanh.

Runtime without communication dung:

```text
max compute time across ranks
```

Khong dung average, vi distributed job phai cho rank cham nhat.
