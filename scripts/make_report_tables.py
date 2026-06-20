from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def fnum(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def inum(value: str, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def fmt(value: float) -> str:
    if abs(value) >= 1000.0:
        return f"{value:.1f}"
    if abs(value) >= 10.0:
        return f"{value:.2f}"
    return f"{value:.4f}"


def rank_comm_ms(row: dict[str, str]) -> float:
    if row.get("comm_ms", "") != "":
        return fnum(row.get("comm_ms", "0"))
    return (
        fnum(row.get("bcast_ms", "0"))
        + fnum(row.get("gather_ms", "0"))
        + fnum(row.get("reduce_ms", "0"))
    )


def rank_idle_pct(row: dict[str, str]) -> float:
    if row.get("idle_pct", "") != "":
        return fnum(row.get("idle_pct", "0"))
    compute = fnum(row.get("compute_ms", "0"))
    idle = fnum(row.get("idle_ms", "0"))
    denom = compute + idle
    return 100.0 * idle / denom if denom > 0 else 0.0


def pct_from_row(row: dict[str, str], key: str) -> float:
    if row.get(key, "") != "":
        return fnum(row.get(key, "0"))
    compute = fnum(row.get("compute_ms", "0"))
    comm = rank_comm_ms(row)
    denom = compute + comm
    if denom <= 0:
        return 0.0
    if key == "compute_pct":
        return 100.0 * compute / denom
    if key == "comm_pct":
        return 100.0 * comm / denom
    return 0.0


def table(headers: list[str], rows: Iterable[list[str]]) -> str:
    out = []
    out.append("| " + " | ".join(headers) + " |")
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out) + "\n"


def write(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body}", encoding="utf-8")
    print(f"TABLE_OK={path}")


def latest_by_run(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    if not rows:
        return []
    run_id = rows[-1].get("run_id", "")
    return [r for r in rows if r.get("run_id", "") == run_id]


def idle_gap_pct_by_run(input_dir: Path) -> dict[str, float]:
    by_run: dict[str, list[dict[str, str]]] = {}
    for row in read_rows(input_dir / "rank_metrics.csv"):
        by_run.setdefault(row.get("run_id", ""), []).append(row)

    out: dict[str, float] = {}
    for run_id, rows in by_run.items():
        if not run_id or not rows:
            continue
        max_compute = max(fnum(r.get("compute_ms", "0")) for r in rows)
        idle_values = [fnum(r.get("idle_ms", "0")) for r in rows]
        if max_compute > 0 and idle_values:
            out[run_id] = (max(idle_values) - min(idle_values)) / max_compute
        else:
            out[run_id] = 0.0
    return out


def make_correctness(input_dir: Path, output_dir: Path) -> bool:
    rows = read_rows(input_dir / "unit_summary.csv")
    if not rows:
        rows = read_rows(input_dir / "demo_correctness.csv")
    if not rows:
        print("TABLE_SKIP=correctness missing unit_summary.csv/demo_correctness.csv")
        return False

    by_algo: dict[str, dict[str, float]] = {}
    for row in rows:
        algo = row.get("algorithm", "unknown")
        cur = by_algo.setdefault(algo, {"max_abs": 0.0, "rel_l2": 0.0, "count": 0.0})
        cur["max_abs"] = max(cur["max_abs"], fnum(row.get("max_abs_error", "0")))
        cur["rel_l2"] = max(cur["rel_l2"], fnum(row.get("relative_l2_error", "0")))
        cur["count"] += 1.0

    body = table(
        ["algorithm", "cases", "max_abs_error", "relative_l2_error", "status"],
        [
            [
                algo,
                str(int(stats["count"])),
                fmt(stats["max_abs"]),
                fmt(stats["rel_l2"]),
                "PASS" if stats["max_abs"] <= 1e-4 and stats["rel_l2"] <= 1e-4 else "CHECK",
            ]
            for algo, stats in sorted(by_algo.items())
        ],
    )
    write(output_dir / "correctness.md", "Correctness Summary", body)
    return True


def make_speedup(input_dir: Path, output_dir: Path) -> bool:
    rows = read_rows(input_dir / "speedup.csv")
    if not rows:
        print("TABLE_SKIP=speedup missing speedup.csv")
        return False

    rows = sorted(rows, key=lambda r: inum(r.get("world_size", "0")))
    t1_comm = fnum(rows[0].get("total_ms_with_comm", "0"))
    t1_no = fnum(rows[0].get("total_ms_without_comm", "0"))
    body_rows = []
    for row in rows:
        p = max(1, inum(row.get("world_size", "1")))
        t_comm = fnum(row.get("total_ms_with_comm", "0"))
        t_no = fnum(row.get("total_ms_without_comm", "0"))
        s_comm = t1_comm / t_comm if t_comm > 0 else 0.0
        s_no = t1_no / t_no if t_no > 0 else 0.0
        body_rows.append(
            [
                str(p),
                fmt(t_comm),
                fmt(t_no),
                fmt(s_comm),
                fmt(s_no),
                fmt(s_comm / p),
                fmt(s_no / p),
            ]
        )
    body = table(
        [
            "processes",
            "runtime_with_comm_ms",
            "runtime_without_comm_ms",
            "speedup_with_comm",
            "speedup_without_comm",
            "eff_with_comm",
            "eff_without_comm",
        ],
        body_rows,
    )
    write(output_dir / "speedup.md", "Speedup And Efficiency", body)
    return True


def make_granularity(input_dir: Path, output_dir: Path) -> bool:
    rows = read_rows(input_dir / "granularity.csv")
    if not rows:
        print("TABLE_SKIP=granularity missing granularity.csv")
        return False
    idle_gap = idle_gap_pct_by_run(input_dir)
    rows = sorted(rows, key=lambda r: (r.get("assignment", ""), inum(r.get("Br", "0"))))
    body = table(
        ["assignment", "Br", "runtime_without_comm_ms", "load_imbalance", "idle_gap_pct", "status"],
        [
            [
                r.get("assignment", ""),
                r.get("Br", ""),
                fmt(fnum(r.get("total_ms_without_comm", "0"))),
                fmt(fnum(r.get("load_imbalance", "0"))),
                fmt(idle_gap.get(r.get("run_id", ""), 0.0)),
                "OK"
                if fnum(r.get("load_imbalance", "0")) <= 1.25
                and idle_gap.get(r.get("run_id", ""), 0.0) <= 0.25
                else "ADJUST",
            ]
            for r in rows
        ],
    )
    write(output_dir / "granularity.md", "Granularity And Load Balance", body)
    return True


def make_rank_breakdown(input_dir: Path, output_dir: Path) -> bool:
    rows = latest_by_run(read_rows(input_dir / "rank_metrics.csv"))
    if not rows:
        print("TABLE_SKIP=rank_breakdown missing rank_metrics.csv")
        return False
    body = table(
        [
            "rank",
            "hostname",
            "rows",
            "compute_ms",
            "comm_ms",
            "idle_ms",
            "compute_pct",
            "comm_pct",
            "idle_pct",
        ],
        [
            [
                r.get("rank", ""),
                r.get("hostname", ""),
                r.get("rows_assigned", ""),
                fmt(fnum(r.get("compute_ms", "0"))),
                fmt(rank_comm_ms(r)),
                fmt(fnum(r.get("idle_ms", "0"))),
                fmt(pct_from_row(r, "compute_pct")),
                fmt(pct_from_row(r, "comm_pct")),
                fmt(rank_idle_pct(r)),
            ]
            for r in rows
        ],
    )
    write(output_dir / "rank_breakdown.md", "Latest Rank Breakdown", body)
    return True


def make_comm_strategy(input_dir: Path, output_dir: Path) -> bool:
    rows = read_rows(input_dir / "comm_strategy.csv")
    if not rows:
        print("TABLE_SKIP=comm_strategy missing comm_strategy.csv")
        return False
    body = table(
        ["algorithm", "processes", "compute_ms", "comm_ms", "total_ms"],
        [
            [
                r.get("algorithm", ""),
                r.get("world_size", ""),
                fmt(fnum(r.get("compute_ms_max", "0"))),
                fmt(fnum(r.get("comm_ms_total", "0"))),
                fmt(fnum(r.get("total_ms_with_comm", "0"))),
            ]
            for r in rows
        ],
    )
    write(output_dir / "communication.md", "Communication Strategy", body)
    return True


def make_thread_scaling(input_dir: Path, output_dir: Path) -> bool:
    rows = read_rows(input_dir / "thread_scaling.csv")
    if not rows:
        print("TABLE_SKIP=thread_scaling missing thread_scaling.csv")
        return False
    rows = sorted(rows, key=lambda r: int(fnum(r.get("omp_threads", "0"))))
    first = rows[0]
    base_comm = fnum(first.get("total_ms_with_comm", "0"))
    body = table(
        ["threads_per_rank", "processes", "runtime_with_comm_ms", "runtime_without_comm_ms", "speedup_vs_T1"],
        [
            [
                r.get("omp_threads", ""),
                r.get("world_size", ""),
                fmt(fnum(r.get("total_ms_with_comm", "0"))),
                fmt(fnum(r.get("total_ms_without_comm", "0"))),
                fmt(base_comm / fnum(r.get("total_ms_with_comm", "1"), 1.0)),
            ]
            for r in rows
        ],
    )
    write(output_dir / "thread_scaling.md", "OpenMP Thread Scaling", body)
    return True


def make_index(output_dir: Path, made: list[str]) -> None:
    body = "\n".join(f"- `{name}.md`" for name in made)
    write(output_dir / "README.md", "Report Tables", body + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/raw")
    parser.add_argument("--output", default="results/tables")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    made: list[str] = []
    for name, fn in [
        ("correctness", make_correctness),
        ("speedup", make_speedup),
        ("granularity", make_granularity),
        ("rank_breakdown", make_rank_breakdown),
        ("communication", make_comm_strategy),
        ("thread_scaling", make_thread_scaling),
    ]:
        if fn(input_dir, output_dir):
            made.append(name)
    make_index(output_dir, made)
    print("REPORT_TABLES_DONE=YES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
