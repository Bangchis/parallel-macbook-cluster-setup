# Rubric Mapping

Use this checklist before submission.

## Cluster Requirement

Requirement:

- At least 3 physical machines.
- One Ubuntu VM per physical machine.
- OpenMPI runs across `master`, `node1`, and `node2`.

Evidence:

- `results/final_.../evidence/cluster_evidence.txt`
- `results/final_.../evidence/hosts.used`
- `results/final_.../raw/rank_metrics.csv`
- `results/final_.../readiness.md`
- `results/latest_preflight.md`

Expected proof:

- `mpirun hostname` shows `master`, `node1`, and `node2`.
- `rank_metrics.csv` shows rows assigned to ranks on all hostnames.
- `EXPERIMENT_PREFLIGHT_STATUS=PASS` before the long benchmark.

## Correctness

Requirement:

- Parallel output must match a serial baseline.

Evidence:

- `results/final_.../raw/demo_correctness.csv`
- `results/final_.../tables/correctness.md`

Expected proof:

- `CORRECTNESS_PASS=YES`
- Small `max_abs_error`, `mean_abs_error`, and `relative_l2_error`.

## Parallel Level

Requirement:

- Explain task-level or data-level parallelism.

Evidence:

- `docs/attention/02_MPI_OPENMP_DESIGN.md`
- `report/FINAL_REPORT_TEMPLATE.md`

Answer:

- Data-level parallelism over query rows.
- OpenMP further splits local rows inside each MPI rank.

## Decomposition

Requirement:

- Explain decomposition technique.

Evidence:

- `src/attention_mpi.cpp`
- `docs/attention/02_MPI_OPENMP_DESIGN.md`

Answer:

- 1D row decomposition over global query rows.

## Mapping

Requirement:

- Explain how work is assigned to processes/processors.

Evidence:

- `row_belongs_to_rank` in `src/attention_mpi.cpp`
- `results/final_.../raw/rank_metrics.csv`
- `results/final_.../figures/05_rank_breakdown.png`

Answer:

- contiguous, cyclic, and block-cyclic mapping.
- Main strategy: `block_id = global_row / Br`, `owner = block_id % world_size`.

## Communication

Requirement:

- Explain blocking/non-blocking communication.

Evidence:

- `src/attention_mpi.cpp`
- `results/final_.../figures/10_comm_strategy.png`
- `results/final_.../tables/communication.md`

Answer:

- Blocking: `MPI_Bcast`, `MPI_Reduce`, `MPI_Gather`.
- Non-blocking comparison: `MPI_Ibcast`, `MPI_Ireduce`.

## Load Balancing And Granularity

Requirement:

- Plot per-process runtime with compute and communication.
- Adjust granularity if idle-time difference is too high.

Evidence:

- `results/final_.../figures/05_rank_breakdown.png`
- `results/final_.../figures/06_granularity_load_balance.png`
- `results/final_.../tables/granularity.md`
- `results/final_.../tables/analysis.md`

Expected proof:

- `load_imbalance <= 1.25` is preferred.
- If not, explain the chosen `Br` and why more tuning is needed.

## Find N

Requirement:

- Use total physical cores and choose N so runtime is around 2-3 minutes.

Evidence:

- `results/final_.../raw/find_N.csv`
- `results/final_.../figures/01_runtime_vs_L.png`
- `results/final_.../experiment_summary.env`
- `results/final_.../tables/analysis.md`
- `results/final_.../tables/experiment_advisor.md`

Expected proof:

- `ATTN_SELECTED_N=...`
- Runtime with communication is near 120-180 seconds.

## Speedup

Requirement:

- Use input size `2N`.
- Vary process counts `1,2,4,8,...,total cores`.
- Plot runtime and speedup with/without communication.

Evidence:

- `results/final_.../raw/speedup.csv`
- `results/final_.../figures/02_runtime_with_without_comm.png`
- `results/final_.../figures/03_speedup.png`
- `results/final_.../figures/04_efficiency.png`
- `results/final_.../tables/speedup.md`

## Hybrid MPI + OpenMP

Requirement:

- The topic is Hybrid MPI + OpenMP.

Evidence:

- `src/attention_mpi.cpp`
- `src/attention_omp.cpp`
- `results/final_.../figures/11_thread_scaling.png`
- `results/final_.../tables/thread_scaling.md`

Expected proof:

- MPI spreads query rows across machines.
- OpenMP spreads local rows across threads inside each rank.

## Code Contribution

Requirement:

- Around 1000+ meaningful lines for group of 4.
- Each member should be able to explain their part.

Evidence:

- `docs/attention/04_MEMBER_TASKS.md`
- `results/final_.../readiness.md`

Expected proof:

- Readiness line count check passes.
- Each member has assigned files and concepts.

## Report

Requirement:

- 10-20 pages, max 20.
- Must include pseudocode, design, experiments, plots, and discussion.

Evidence:

- `report/FINAL_REPORT_TEMPLATE.md`
- `results/final_.../report/final_report_draft.md`
- `docs/attention/08_REPORT_OUTLINE.md`
- `results/final_.../tables/analysis.md`

## Demo

Requirement:

- Offline demo must run on MPI cluster and show ranks on all machines.

Evidence:

- `docs/attention/10_FINAL_DEMO_SCRIPT.md`
- `results/demo_.../demo_summary.md`
- `results/demo_.../demo_terminal.log`
- `results/final_.../evidence/cluster_evidence.txt`
- `results/final_.../readiness.md`
