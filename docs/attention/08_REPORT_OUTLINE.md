# Report Outline 10-20 Pages

Target length: 15-17 pages.

Use `report/FINAL_REPORT_TEMPLATE.md` as the starting draft.

## 1. Introduction

- Course project goal.
- Why self-attention is interesting.
- Clarify that this is not Transformer training.

## 2. Cluster Setup

- 3 physical MacBooks.
- One Ubuntu VM per machine.
- OpenMPI across `master`, `node1`, `node2`.
- Include screenshot/log of hostname/rank test.

## 3. Algorithm

- Tensor shapes.
- Self-attention formula.
- Complexity `O(B * H * L^2 * Dh)`.
- Memory issue of naive attention.

## 4. Parallel Design

Must explicitly mention:

- parallel level: data-level parallelism over query rows.
- decomposition: 1D row/block decomposition.
- mapping: contiguous, cyclic, block_cyclic.
- communication: blocking `MPI_Bcast`, `MPI_Reduce`, `MPI_Gather`.
- OpenMP inside each rank.

## 5. Pseudocode

Include pseudocode:

```text
rank 0 generates Q,K,V
broadcast Q,K,V
for each rank:
  select rows by block_cyclic mapping
  OpenMP parallel for over local rows:
    compute online softmax row
reduce output/checksum
gather metrics
```

## 6. Correctness

- Compare parallel output with serial baseline.
- Report max abs error, mean abs error, relative L2.

## 7. Experiments

- Find N.
- Granularity/load balance.
- Speedup.
- Memory comparison.
- Communication strategy comparison.

## 8. Results

Use plots from `results/figures`.

Discuss:

- communication overhead
- blocking vs non-blocking MPI communication
- speedup trend
- efficiency trend
- load imbalance and `Br`

## 9. Member Contributions

Map members to files and concepts.

## 10. Conclusion

- What worked.
- What limits the speedup.
- Future work: non-blocking communication, 2D decomposition, GPU.
