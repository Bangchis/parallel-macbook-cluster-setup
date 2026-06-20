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

Then check the config before spending time on a long benchmark:

```bash
python3 scripts/check_experiment_config.py --config configs/attention_experiment.env
```

Expected: `EXPERIMENT_PREFLIGHT_STATUS=PASS`. Warnings are acceptable only if
the group understands them, for example when running a local smoke test without
the full 3-machine hostfile.

## 3. Sanity Check Cluster

Before the group meets, each member can run a tiny local smoke test:

```bash
bash scripts/run_local_final_smoke.sh
```

This does not replace the final 3-machine benchmark. It only checks that the
pipeline, plots, tables, analysis, readiness checker, and packaging workflow
are wired correctly on one machine.

From master:

```bash
mpirun -np 3 --hostfile configs/hosts hostname
```

Expected: output includes `master`, `node1`, and `node2`.

## 4. Run Required Experiments

From master:

```bash
python3 scripts/check_experiment_config.py \
  --config configs/attention_experiment.env \
  --output results/latest_preflight.md
bash scripts/run_required_experiments.sh
```

The script runs:

1. cluster evidence collection
2. correctness demo
3. find N with total physical cores
4. granularity/load-balance test at N
5. speedup test at 2N
6. block-size, memory, communication-strategy, OpenMP thread comparisons
7. report figures and tables

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
report/final_report_draft.md
evidence/cluster_evidence.txt
evidence/hosts.used
experiment_summary.env
readiness.md
```

Use `evidence/cluster_evidence.txt` to prove OpenMPI, hostfile, CPU info, and
the `mpirun hostname` test.
Use `experiment_summary.env` to report the selected N and 2N.
Use `tables/analysis.md` for the main result discussion.
Use `report/final_report_draft.md` as the first full report draft, then edit
names, screenshots, final discussion, and formatting before submission.
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

## 7. Create Submission Package

After readiness is acceptable:

```bash
bash scripts/make_submission_package.sh --run-dir results/final_YYYYMMDD-HHMMSS
```

This creates:

```text
submission/attention_project_submission_YYYYMMDD-HHMMSS/
submission/attention_project_submission_YYYYMMDD-HHMMSS.tar.gz
```
