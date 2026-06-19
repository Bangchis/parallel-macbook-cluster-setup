#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass

from mpi4py import MPI


@dataclass(frozen=True)
class Block:
    start: int
    count: int

    @property
    def end(self) -> int:
        return self.start + self.count - 1


def block_range(n: int, rank: int, size: int) -> Block:
    base = n // size
    rem = n % size
    count = base + (1 if rank < rem else 0)
    start = rank * base + min(rank, rem)
    return Block(start=start, count=count)


def ordered_print(comm: MPI.Comm, line: str) -> None:
    rank = comm.Get_rank()
    size = comm.Get_size()
    for owner in range(size):
        comm.Barrier()
        if owner == rank:
            print(line, flush=True)
    comm.Barrier()


def matrix_value(row: int, col: int) -> int:
    return (row + 1) * 10 + (col + 1)


def vector_value(col: int) -> int:
    return col + 1


def lcg_next(state: int) -> int:
    return (state * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)


def unit_random(state: int) -> tuple[float, int]:
    state = lcg_next(state)
    value = state >> 11
    return value / float(1 << 53), state


def test_rank_placement(comm: MPI.Comm, host: str) -> bool:
    rank = comm.Get_rank()
    size = comm.Get_size()
    hosts = comm.gather(host, root=0)

    passed = False
    if rank == 0:
        print("\n[PYTEST rank_placement]", flush=True)
        assert hosts is not None
        for idx, node_host in enumerate(hosts):
            print(f"rank={idx} host={node_host}", flush=True)
        unique_hosts = len(set(hosts))
        passed = size >= 3 and unique_hosts >= 3
        print(
            f"unique_hosts={unique_hosts} expected_at_least=3 "
            f"status={'PASS' if passed else 'FAIL'}",
            flush=True,
        )

    return bool(comm.bcast(passed, root=0))


def test_distributed_sum(comm: MPI.Comm, host: str, n: int) -> bool:
    rank = comm.Get_rank()
    size = comm.Get_size()
    block = block_range(n, rank, size)

    first = block.start + 1
    last = block.start + block.count
    local_sum = 0
    if block.count > 0:
        local_sum = (first + last) * block.count // 2

    mpi_sum = comm.reduce(local_sum, op=MPI.SUM, root=0)

    if rank == 0:
        print("\n[PYTEST distributed_sum]", flush=True)

    ordered_print(
        comm,
        f"rank={rank} host={host} range=[{first if block.count else 0},"
        f"{last if block.count else -1}] local_sum={local_sum}",
    )

    passed = False
    if rank == 0:
        expected = n * (n + 1) // 2
        passed = mpi_sum == expected
        print(
            f"N={n} expected={expected} mpi_sum={mpi_sum} "
            f"status={'PASS' if passed else 'FAIL'}",
            flush=True,
        )

    return bool(comm.bcast(passed, root=0))


def test_matrix_vector_checksum(comm: MPI.Comm, host: str, rows: int, cols: int) -> bool:
    rank = comm.Get_rank()
    size = comm.Get_size()
    block = block_range(rows, rank, size)

    local_checksum = 0
    for row in range(block.start, block.start + block.count):
        y = 0
        for col in range(cols):
            y += matrix_value(row, col) * vector_value(col)
        local_checksum += y

    checksum = comm.reduce(local_checksum, op=MPI.SUM, root=0)

    if rank == 0:
        print("\n[PYTEST matrix_vector_checksum]", flush=True)

    ordered_print(
        comm,
        f"rank={rank} host={host} rows=[{block.start if block.count else 0},"
        f"{block.end if block.count else -1}] local_checksum={local_checksum}",
    )

    passed = False
    if rank == 0:
        expected = 0
        for row in range(rows):
            for col in range(cols):
                expected += matrix_value(row, col) * vector_value(col)
        passed = checksum == expected
        print(
            f"rows={rows} cols={cols} expected_checksum={expected} "
            f"mpi_checksum={checksum} status={'PASS' if passed else 'FAIL'}",
            flush=True,
        )

    return bool(comm.bcast(passed, root=0))


def test_monte_carlo_pi(comm: MPI.Comm, host: str, samples_total: int) -> bool:
    rank = comm.Get_rank()
    size = comm.Get_size()
    block = block_range(samples_total, rank, size)

    state = 0x9E3779B97F4A7C15 ^ ((rank + 1) * 0xBF58476D1CE4E5B9)
    inside = 0
    for _ in range(block.count):
        x, state = unit_random(state)
        y, state = unit_random(state)
        if x * x + y * y <= 1.0:
            inside += 1

    total_inside = comm.reduce(inside, op=MPI.SUM, root=0)

    if rank == 0:
        print("\n[PYTEST monte_carlo_pi]", flush=True)

    ordered_print(comm, f"rank={rank} host={host} samples={block.count} inside={inside}")

    passed = False
    if rank == 0:
        pi_estimate = 4.0 * total_inside / samples_total
        passed = 3.10 <= pi_estimate <= 3.18
        print(
            f"samples={samples_total} inside={total_inside} "
            f"pi_estimate={pi_estimate:.6f} accepted_range=[3.10,3.18] "
            f"status={'PASS' if passed else 'FAIL'}",
            flush=True,
        )

    return bool(comm.bcast(passed, root=0))


def main() -> int:
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    host = MPI.Get_processor_name()

    sum_n = 1_000_000
    matrix_rows = 12
    matrix_cols = 8
    pi_samples = 300_000

    if rank == 0:
        print(f"PYTHON_PARALLEL_UNIT_TESTS_START size={size}", flush=True)
        print(
            f"args sum_n={sum_n} matrix_rows={matrix_rows} "
            f"matrix_cols={matrix_cols} pi_samples={pi_samples}",
            flush=True,
        )

    results = [
        test_rank_placement(comm, host),
        test_distributed_sum(comm, host, sum_n),
        test_matrix_vector_checksum(comm, host, matrix_rows, matrix_cols),
        test_monte_carlo_pi(comm, host, pi_samples),
    ]
    overall = all(results)

    if rank == 0:
        print(f"\nPYTHON_PARALLEL_UNIT_TESTS_OVERALL={'PASS' if overall else 'FAIL'}", flush=True)

    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
