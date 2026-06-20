# Final Experiment Pipeline

Use this when all 3 MacBooks are on the same LAN and MPI already works.

## 1. Pull And Build

On every VM:

```bash
cd ~/parallel-macbook-cluster-setup
git pull
bash scripts/build.sh
```

On the master VM:

```bash
bash scripts/install_plot_deps.sh
```

## 2. Prepare Experiment Config

On the master VM:

```bash
cp configs/attention_experiment.env.example configs/attention_experiment.env
nano configs/attention_experiment.env
```

Edit these values:

- `MPI_LAN_CIDR`: current LAN subnet, for example `192.168.31.0/24`.
- `ATTN_TOTAL_PROCS`: total physical CPU cores across all machines.
- `ATTN_P_LIST`: `1 2 4 8 ... total_procs`.
- `ATTN_FIND_N_LIST`: candidate sequence lengths for finding N.

Keep `ATTN_THREADS=1` for the required process-count experiments.

## 3. Sanity Check Cluster

From master:

```bash
mpirun -np 3 --hostfile configs/hosts hostname
```

Expected: output includes `master`, `node1`, and `node2`.

## 4. Run Required Experiments

From master:

```bash
bash scripts/run_required_experiments.sh
```

The script runs:

1. correctness demo
2. find N with total physical cores
3. granularity/load-balance test at N
4. speedup test at 2N
5. block-size, memory, communication-strategy, OpenMP thread comparisons
6. report figures and tables

## 5. Outputs

The script creates a new directory:

```text
results/final_YYYYMMDD-HHMMSS/
```

Important files:

```text
raw/*.csv
figures/*.png
tables/*.md
experiment_summary.env
readiness.md
```

Use `experiment_summary.env` to report the selected N and 2N.
Use `tables/analysis.md` for the main result discussion.
Use `readiness.md` as the final checklist before submission.

For the final cluster run, verify all 3 hostnames explicitly:

```bash
python3 scripts/check_final_readiness.py \
  --run-dir results/final_YYYYMMDD-HHMMSS \
  --require-host master \
  --require-host node1 \
  --require-host node2
```

## 6. If N Is Too Small Or Too Large

Open:

```text
results/final_.../raw/find_N.csv
```

If no row is close to 2-3 minutes, edit:

```bash
nano configs/attention_experiment.env
```

Increase or decrease:

```bash
ATTN_FIND_N_LIST="..."
```

Then rerun:

```bash
bash scripts/run_required_experiments.sh
```
