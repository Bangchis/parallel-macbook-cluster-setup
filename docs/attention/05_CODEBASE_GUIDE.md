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
- Broadcast Q/K/V, compute local rows, reduce output, gather metrics.
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
