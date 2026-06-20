# Codebase Guide

Doc nay giup moi thanh vien biet file nao lam gi va nen debug o dau.

## Core Data And Config

`src/tensor.hpp/cpp`

- Defines `Tensor4D`.
- Index order: `B x H x L x Dh`.
- Common bug: sai cong thuc index hoac nham `i` voi `d`.

`src/config.hpp/cpp`

- Parses CLI options.
- Sets OpenMP thread count and schedule.
- Common bug: ranks chay config khac nhau trong MPI.

## Attention Algorithms

`src/attention_serial.hpp/cpp`

- `attn_full`: oracle, luu full `S` va `P`.
- `attn_row`: baseline row-wise.
- Common bug: softmax thieu stable max.

`src/attention_online.hpp/cpp`

- `attn_online_row`: blocked online softmax cho mot output row.
- Common bug: quen rescale `l` va `out` khi `m_new` thay doi.

`src/attention_omp.hpp/cpp`

- `attn_omp_row`.
- `attn_omp_online`.
- Common bug: shared buffer giua threads. Code hien tai dung private buffers.

`src/attention_mpi.hpp/cpp`

- `attn_mpi_row`.
- `attn_mpi_online`.
- `attn_mpi_row_nb`.
- `attn_mpi_online_nb`.
- Broadcast Q/K/V, compute local rows, reduce output, gather metrics.
- `_nb` variants use non-blocking MPI collectives for communication comparison.
- Common bug: sai row mapping hoac hostfile sai.

## Correctness, Metrics, CSV

`src/correctness.hpp/cpp`

- `check_error`.
- `checksum`.
- Metrics: max abs, mean abs, relative L2.

`src/metrics.hpp/cpp`

- `Metrics`, `RankStat`, `ThreadStat`.
- Timing helpers.

`src/csv_writer.hpp/cpp`

- Writes `summary.csv`, `rank_metrics.csv`, `thread_metrics.csv`.

`src/memory_model.hpp/cpp`

- Estimates naive, row-wise, online memory.

`scripts/make_report_tables.py`

- Converts benchmark CSV files into markdown tables for the report.
- Does not require pandas.

`scripts/analyze_final_results.py`

- Converts benchmark CSV files into a short written analysis for the report.
- Summarizes selected N, speedup, load balance, block size, communication, and
  cluster hostnames.

`scripts/run_report_artifacts.sh`

- Generates plots, markdown tables, and `analysis.md` after experiments finish.

`scripts/run_required_experiments.sh`

- Runs the final required experiment pipeline.
- Selects N from `find_N.csv`, runs granularity at N, speedup at 2N, then
  generates report artifacts.

`scripts/run_local_final_smoke.sh`

- Runs a tiny one-machine version of the final pipeline for pre-flight checks.

`scripts/run_final_demo.sh`

- Runs a short demo that builds the benchmark, prints MPI hostnames, runs the
  correctness demo, and writes a demo summary.
- Use this during the live demo before showing the long final benchmark plots.

`scripts/summarize_demo_run.py`

- Reads `demo_correctness.csv`, `rank_metrics.csv`, and MPI hostname evidence.
- Writes `demo_summary.md` with correctness, hostnames, rank work, and timing.

`scripts/check_experiment_config.py`

- Checks the final experiment config before the long cluster benchmark.
- Verifies MPI tools, hostfile shape, process counts, N-search settings, and
  required scripts.

`scripts/run_thread_sweep.sh`

- Varies OpenMP threads per rank for the hybrid MPI + OpenMP experiment.

`scripts/collect_final_evidence.sh`

- Captures cluster evidence: hostfile, OpenMPI version, CPU information, git
  commit, and `mpirun hostname`.

`scripts/check_final_readiness.py`

- Checks whether a final run directory has required CSV files, plots, tables,
  correctness evidence, selected N, rank hostnames, and code line count.

`scripts/make_submission_package.sh`

- Creates a submission folder and `.tar.gz` archive with source, docs, report
  template, and optional final results.

`configs/attention_experiment.env.example`

- Template for the final cluster benchmark settings.

`report/FINAL_REPORT_TEMPLATE.md`

- Report draft aligned with the professor's requirements.

`docs/attention/11_RUBRIC_MAPPING.md`

- Maps each professor requirement to code files, result files, and report
  evidence.

## Main Program

`src/main.cpp`

- MPI init/finalize.
- parse config.
- generate Q/K/V on rank 0.
- dispatch algorithm.
- verify output.
- write CSV.

Do not put algorithm loops directly in `main.cpp`; add helpers in the right
algorithm file.
