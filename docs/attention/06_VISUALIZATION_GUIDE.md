# Visualization Guide

Plots are generated from CSV files in `results/raw/`.

Install dependencies:

```bash
bash scripts/install_plot_deps.sh
```

Generate all plots:

```bash
.venv-plot/bin/python plots/plot_all.py --input results/raw --output results/figures
```

Generate plots and markdown tables for the report:

```bash
bash scripts/run_report_artifacts.sh
```

The final pipeline writes artifacts under `results/final_YYYYMMDD-HHMMSS/`.

## Required Figures

`01_runtime_vs_L.png`

- Reads `find_N.csv`.
- Shows attention runtime grows near `L^2`.

`02_runtime_with_without_comm.png`

- Reads `speedup.csv`.
- Compares total runtime with communication and compute-only runtime.

`03_speedup.png`

- Reads `speedup.csv`.
- Uses `T1 / Tp`.

`04_efficiency.png`

- Reads `speedup.csv`.
- Uses `speedup / P`.

`05_rank_breakdown.png`

- Reads `rank_metrics.csv`.
- Stacked bar of compute, broadcast, gather, reduce.

`06_granularity_load_balance.png`

- Reads `granularity.csv`.
- Shows load imbalance for different `Br` and assignment strategies.

`07_memory_comparison.png`

- Reads `summary.csv`.
- Shows estimated memory for algorithms.

`08_blocksize_heatmap.png`

- Reads `blocksize.csv`.
- Shows runtime for `Br x Bc`.

`09_attention_heatmap.png`

- Reads `attention_dump.csv`.
- Only for small debug/demo input.

`10_comm_strategy.png`

- Reads `comm_strategy.csv`.
- Compares blocking and non-blocking MPI communication overhead.

## Report Advice

Every figure should answer one question:

- Does runtime grow with L?
- How much communication overhead exists?
- Does adding processes improve runtime?
- Is load balanced?
- Does online softmax reduce memory?
- Does changing MPI communication strategy help?

Markdown tables are generated in `results/tables/`:

- `analysis.md`
- `correctness.md`
- `speedup.md`
- `granularity.md`
- `rank_breakdown.md`
- `communication.md`
