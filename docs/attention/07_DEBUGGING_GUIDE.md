# Debugging Guide

## Tensor Bugs

Use small input:

```bash
./build/attention_bench --algo serial_row --B 1 --H 1 --L 4 --Dh 4 --verify 1 --debug 1
```

Check:

- tensor shape printed correctly
- no crash in `Tensor4D::idx`
- `CORRECTNESS_PASS=YES`

## Softmax Bugs

Symptoms:

- NaN output
- very large error
- causal result differs only on future tokens

Check:

- divide score by `sqrt(Dh)`
- subtract max before `exp`
- denominator is not zero

## Online Softmax Bugs

Common mistakes:

- forgot `alpha = exp(m - m_new)`
- forgot to rescale `out`
- final divide by `l` too early
- causal block beyond `i` not skipped

Compare:

```bash
./build/attention_bench --algo omp_online --B 1 --H 2 --L 64 --Dh 32 --verify 1
```

## OpenMP Bugs

Symptoms:

- nondeterministic error
- pass once, fail later

Check:

- scores/out buffers are private to each thread
- each row writes unique output row
- no print inside compute loop

## MPI Bugs

Check hosts:

```bash
mpirun -np 3 --hostfile configs/hosts hostname
```

Check correctness:

```bash
bash scripts/run_demo_correctness.sh
```

Common issues:

- hostfile slots wrong
- VM IP changed
- `/shared/mpi` not mounted
- ranks use different binary
- output gather/reduce size mismatch

## Benchmark Bugs

Avoid:

- timing data generation
- printing inside timed region
- using average rank compute time as parallel runtime

Use:

```text
total_ms_without_comm = max compute time across ranks
```
