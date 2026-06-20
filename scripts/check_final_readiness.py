from __future__ import annotations

import argparse
import csv
from pathlib import Path


REQUIRED_RAW = [
    "demo_correctness.csv",
    "find_N.csv",
    "granularity.csv",
    "speedup.csv",
    "blocksize.csv",
    "memory.csv",
    "comm_strategy.csv",
    "rank_metrics.csv",
    "summary.csv",
]

REQUIRED_FIGURES = [
    "01_runtime_vs_L.png",
    "02_runtime_with_without_comm.png",
    "03_speedup.png",
    "04_efficiency.png",
    "05_rank_breakdown.png",
    "06_granularity_load_balance.png",
    "07_memory_comparison.png",
    "08_blocksize_heatmap.png",
    "09_attention_heatmap.png",
    "10_comm_strategy.png",
]

REQUIRED_TABLES = [
    "analysis.md",
    "correctness.md",
    "speedup.md",
    "granularity.md",
    "rank_breakdown.md",
    "communication.md",
]


def read_csv(path: Path) -> list[dict[str, str]]:
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


def newest_final_dir(results_dir: Path) -> Path | None:
    candidates = [p for p in results_dir.glob("final_*") if p.is_dir()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def count_lines(paths: list[Path]) -> int:
    total = 0
    for path in paths:
        try:
            with path.open(encoding="utf-8", errors="ignore") as f:
                total += sum(1 for line in f if line.strip())
        except OSError:
            pass
    return total


def add(rows: list[tuple[str, str, str]], status: str, item: str, detail: str) -> None:
    rows.append((status, item, detail))


def markdown(rows: list[tuple[str, str, str]]) -> str:
    out = [
        "# Final Readiness Check",
        "",
        "| status | item | detail |",
        "| --- | --- | --- |",
    ]
    for status, item, detail in rows:
        out.append(f"| {status} | {item} | {detail} |")
    out.append("")
    return "\n".join(out)


def check_files(run_dir: Path, rows: list[tuple[str, str, str]]) -> None:
    for name in REQUIRED_RAW:
        path = run_dir / "raw" / name
        add(rows, "PASS" if path.exists() else "FAIL", f"raw/{name}", str(path))
    for name in REQUIRED_FIGURES:
        path = run_dir / "figures" / name
        add(rows, "PASS" if path.exists() else "FAIL", f"figures/{name}", str(path))
    for name in REQUIRED_TABLES:
        path = run_dir / "tables" / name
        add(rows, "PASS" if path.exists() else "FAIL", f"tables/{name}", str(path))
    summary = run_dir / "experiment_summary.env"
    add(rows, "PASS" if summary.exists() else "WARN", "experiment_summary.env", str(summary))


def check_correctness(run_dir: Path, rows: list[tuple[str, str, str]]) -> None:
    demo = read_csv(run_dir / "raw" / "demo_correctness.csv")
    if not demo:
        add(rows, "FAIL", "correctness", "missing demo_correctness.csv rows")
        return
    max_abs = max(fnum(r.get("max_abs_error", "0")) for r in demo)
    rel_l2 = max(fnum(r.get("relative_l2_error", "0")) for r in demo)
    ok = max_abs <= 1e-4 and rel_l2 <= 1e-4
    add(rows, "PASS" if ok else "FAIL", "correctness error", f"max_abs={max_abs:.6g}, rel_l2={rel_l2:.6g}")


def check_speedup(run_dir: Path, rows: list[tuple[str, str, str]]) -> None:
    speed = read_csv(run_dir / "raw" / "speedup.csv")
    if not speed:
        add(rows, "FAIL", "speedup", "missing speedup rows")
        return
    procs = sorted({inum(r.get("world_size", "0")) for r in speed})
    has_serial = 1 in procs
    has_parallel = any(p > 1 for p in procs)
    status = "PASS" if has_serial and has_parallel else "WARN"
    add(rows, status, "speedup process list", "P=" + " ".join(str(p) for p in procs))


def check_load_balance(run_dir: Path, rows: list[tuple[str, str, str]]) -> None:
    gran = read_csv(run_dir / "raw" / "granularity.csv")
    if not gran:
        add(rows, "FAIL", "load balance", "missing granularity rows")
        return
    best = min(fnum(r.get("load_imbalance", "999")) for r in gran)
    status = "PASS" if best <= 1.25 else "WARN"
    add(rows, status, "load imbalance", f"best={best:.4f}, target<=1.25")


def check_cluster_hosts(run_dir: Path, rows: list[tuple[str, str, str]], expected_hosts: list[str]) -> None:
    rank_rows = read_csv(run_dir / "raw" / "rank_metrics.csv")
    hosts = sorted({r.get("hostname", "") for r in rank_rows if r.get("hostname", "")})
    if not expected_hosts:
        status = "PASS" if len(hosts) >= 3 else "WARN"
        add(rows, status, "cluster hostnames", ", ".join(hosts) if hosts else "missing")
        return
    missing = [h for h in expected_hosts if h not in hosts]
    status = "PASS" if not missing else "FAIL"
    detail = "seen=" + ",".join(hosts) + (" missing=" + ",".join(missing) if missing else "")
    add(rows, status, "expected cluster hostnames", detail)


def check_loc(repo: Path, rows: list[tuple[str, str, str]]) -> None:
    files = []
    for folder in ["src", "scripts", "plots", "python_tests"]:
        base = repo / folder
        if base.exists():
            files.extend(p for p in base.rglob("*") if p.suffix in {".cpp", ".hpp", ".sh", ".py"})
    total = count_lines(files)
    add(rows, "PASS" if total >= 1000 else "WARN", "meaningful code line count", f"{total} non-empty lines")


def check_find_n(run_dir: Path, rows: list[tuple[str, str, str]]) -> None:
    summary = run_dir / "experiment_summary.env"
    if not summary.exists():
        add(rows, "WARN", "selected N", "missing experiment_summary.env")
        return
    values: dict[str, str] = {}
    for line in summary.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            values[k] = v
    selected = values.get("ATTN_SELECTED_N", "")
    speedup_l = values.get("ATTN_SPEEDUP_L", "")
    add(rows, "PASS" if selected and speedup_l else "WARN", "selected N and 2N", f"N={selected}, 2N={speedup_l}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--require-host", action="append", default=[])
    args = parser.parse_args()

    repo = Path.cwd()
    if args.run_dir:
        run_dir = Path(args.run_dir)
    else:
        found = newest_final_dir(Path(args.results_dir))
        if found is None:
            print("ERROR: no run dir given and no results/final_* directory found")
            return 1
        run_dir = found

    rows: list[tuple[str, str, str]] = []
    add(rows, "PASS" if run_dir.exists() else "FAIL", "run directory", str(run_dir))
    check_files(run_dir, rows)
    check_correctness(run_dir, rows)
    check_find_n(run_dir, rows)
    check_speedup(run_dir, rows)
    check_load_balance(run_dir, rows)
    check_cluster_hosts(run_dir, rows, args.require_host)
    check_loc(repo, rows)

    text = markdown(rows)
    out = run_dir / "readiness.md"
    out.write_text(text, encoding="utf-8")

    fail = sum(1 for status, _, _ in rows if status == "FAIL")
    warn = sum(1 for status, _, _ in rows if status == "WARN")
    print(f"READINESS_REPORT={out}")
    print(f"FINAL_READINESS_STATUS={'PASS' if fail == 0 else 'FAIL'} FAIL={fail} WARN={warn}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
