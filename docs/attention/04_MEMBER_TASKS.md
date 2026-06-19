# Member Tasks

## Member 1

Files:

- `src/tensor.hpp/cpp`
- `src/config.hpp/cpp`
- `src/attention_serial.hpp/cpp`
- `src/correctness.hpp/cpp`

Must explain:

- Tensor4D index order
- stable softmax
- why `attn_full` is oracle
- max/mean/relative L2 error

## Member 2

Files:

- `src/attention_online.hpp/cpp`
- `src/attention_omp.hpp/cpp`
- `src/metrics.hpp/cpp`

Must explain:

- online softmax `m`, `l`, `alpha`
- causal mask
- OpenMP schedule
- private buffers and no lock

## Member 3

Files:

- `src/attention_mpi.hpp/cpp`
- `src/csv_writer.hpp/cpp`
- MPI parts of `src/main.cpp`

Must explain:

- broadcast Q/K/V
- row mapping strategies
- reduce output/checksum
- gather rank/thread metrics
- communication vs compute timing

## Member 4

Files:

- `scripts/*.sh`
- `plots/*.py`
- `docs/attention/*.md`
- `README.md`

Must explain:

- benchmark workflow
- find N
- speedup and efficiency
- rank breakdown plot
- report figures
