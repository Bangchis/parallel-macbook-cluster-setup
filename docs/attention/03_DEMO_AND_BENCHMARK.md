# Demo And Benchmark Guide

Build:

```bash
bash scripts/build.sh
```

Local correctness:

```bash
bash scripts/run_unit_tests.sh
```

Cluster hostname test:

```bash
mpirun -np 3 --hostfile configs/hosts hostname
```

Correctness demo:

```bash
bash scripts/run_demo_correctness.sh
```

Performance demo:

```bash
bash scripts/run_demo_perf.sh
```

All experiments:

```bash
bash scripts/run_all_experiments.sh
```

Memory comparison only:

```bash
bash scripts/run_memory_comparison.sh
```

Generate plots:

```bash
bash scripts/install_plot_deps.sh
.venv-plot/bin/python plots/plot_all.py --input results/raw --output results/figures
```

## Required Experiments

Find N:

- use total physical cores, for example 12.
- sweep L.
- choose N so runtime is around 2-3 minutes.

Granularity/load balancing:

- use L=N.
- compare `Br` and assignment strategies.
- plot per-rank compute/communication time.

Speedup:

- use L=2N.
- test process counts 1,2,4,8,12 if available.
- plot runtime with and without communication.
- plot speedup and efficiency.

Results live in:

```text
results/raw/
results/figures/
results/tables/
```
