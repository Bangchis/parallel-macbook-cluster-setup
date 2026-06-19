# Chay Unit Test Song Song

File nay tra loi hai cau hoi:

- Chay bai test song song hoa o dau?
- Ket qua in ra va luu o dau?

## Terminal Nam O Dau?

Cluster dang dung Multipass, nen VM Ubuntu master khong co cua so GUI rieng.
Ban mo terminal tu macOS hoac VS Code roi vao master bang:

```bash
multipass shell pp-master
```

Sau lenh nay, prompt se la terminal ben trong Ubuntu VM master.

## Chay Test C 3 May

Trong terminal cua master VM:

```bash
cd ~/parallel-macbook-cluster-setup
git pull
bash scripts/run_parallel_unit_tests.sh
```

Script se:

- Copy `mpi_samples/parallel_unit_tests.c` vao `/shared/mpi`.
- Compile bang `mpicc`.
- Chay `mpirun` tren `master`, `node1`, `node2`.
- In ket qua truc tiep ra terminal master.
- Luu log vao `/shared/mpi/results/<timestamp>-parallel-unit-tests/`.

## Chay Test Python 3 May

Python test dung `mpi4py`. Cai dependency mot lan tren ca 3 VM:

```bash
cd ~/parallel-macbook-cluster-setup
bash scripts/install_python_mpi_deps.sh
```

Sau do chay:

```bash
bash scripts/run_python_parallel_tests.sh
```

Script se:

- Copy `python_tests/parallel_unit_tests.py` vao `/shared/mpi`.
- Chay preflight `mpi4py` tren `master`, `node1`, `node2`.
- Chay unit test Python bang `mpirun`.
- In ket qua truc tiep ra terminal master.
- Luu log vao `/shared/mpi/results/<timestamp>-python-parallel-tests/`.

## Ket Qua Luu O Dau?

Log moi nhat:

```bash
/shared/mpi/results/latest/parallel_unit_tests.log
```

Log Python moi nhat:

```bash
/shared/mpi/results/latest-python/python_parallel_tests.log
```

Xem lai log:

```bash
less /shared/mpi/results/latest/parallel_unit_tests.log
```

Xem lai log Python:

```bash
less /shared/mpi/results/latest-python/python_parallel_tests.log
```

List cac lan chay:

```bash
ls -lah /shared/mpi/results
```

Copy log tu VM ra macOS neu can nop bai:

```bash
exit
multipass transfer pp-master:/shared/mpi/results/latest/parallel_unit_tests.log ~/Desktop/parallel_unit_tests.log
```

Copy log Python:

```bash
multipass transfer pp-master:/shared/mpi/results/latest-python/python_parallel_tests.log ~/Desktop/python_parallel_tests.log
```

## Cac Test Dang Co

`rank_placement`: kiem tra co rank chay tren ca 3 hostname.

`distributed_sum`: chia day `1..N` cho cac rank, moi rank tinh mot doan,
sau do `MPI_Reduce` ve tong cuoi.

`matrix_vector_checksum`: chia cac hang cua ma tran cho cac rank, moi rank
tinh checksum cuc bo, sau do reduce ve checksum toan cuc.

`monte_carlo_pi`: moi rank chay mot phan sample, reduce ve uoc luong pi.

Pass khi thay:

```text
PARALLEL_UNIT_TESTS_OVERALL=PASS
```

Python pass khi thay:

```text
PYTHON_PARALLEL_UNIT_TESTS_OVERALL=PASS
```

Va trong log co rank tren ca 3 may:

```text
rank=0 host=master
rank=1 host=node1
rank=2 host=node2
```
