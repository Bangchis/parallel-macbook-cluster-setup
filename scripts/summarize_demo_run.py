from __future__ import annotations

import argparse
import csv
from pathlib import Path


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


def fmt_ms(value: float) -> str:
    if value >= 1000.0:
        return f"{value / 1000.0:.3f}s"
    return f"{value:.3f}ms"


def table(headers: list[str], rows: list[list[str]]) -> str:
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def latest_run(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    if not rows:
        return []
    run_id = rows[-1].get("run_id", "")
    return [r for r in rows if r.get("run_id", "") == run_id]


def hostnames_from_evidence(path: Path) -> list[str]:
    if not path.exists():
        return []
    hosts = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("COMMAND:"):
            hosts.append(line)
    return hosts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--output", default="")
    parser.add_argument("--require-host", action="append", default=[])
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    raw = run_dir / "raw"
    evidence = run_dir / "evidence"
    output = Path(args.output) if args.output else run_dir / "demo_summary.md"

    correctness_rows = read_rows(raw / "demo_correctness.csv")
    rank_rows = latest_run(read_rows(raw / "rank_metrics.csv"))
    mpi_hosts = hostnames_from_evidence(evidence / "mpi_hostname.txt")
    metric_hosts = sorted({r.get("hostname", "") for r in rank_rows if r.get("hostname", "")})
    seen_hosts = sorted(set(mpi_hosts) | set(metric_hosts))

    missing_hosts = [host for host in args.require_host if host not in seen_hosts]
    errors: list[str] = []
    warnings: list[str] = []

    if not correctness_rows:
        errors.append("missing demo_correctness.csv")
        correctness = {}
    else:
        correctness = correctness_rows[-1]
        max_abs = fnum(correctness.get("max_abs_error", "999"))
        rel_l2 = fnum(correctness.get("relative_l2_error", "999"))
        if max_abs > 1e-4 or rel_l2 > 1e-4:
            errors.append(f"correctness error too high: max_abs={max_abs}, rel_l2={rel_l2}")

    if not rank_rows:
        errors.append("missing rank_metrics.csv")
    if missing_hosts:
        errors.append("missing required hosts: " + ", ".join(missing_hosts))
    if len(seen_hosts) < 3:
        warnings.append("demo saw fewer than 3 distinct hostnames")

    rank_table = table(
        ["rank", "hostname", "rows", "compute", "comm", "idle"],
        [
            [
                r.get("rank", ""),
                r.get("hostname", ""),
                r.get("rows_assigned", ""),
                fmt_ms(fnum(r.get("compute_ms", "0"))),
                fmt_ms(
                    fnum(r.get("bcast_ms", "0"))
                    + fnum(r.get("gather_ms", "0"))
                    + fnum(r.get("reduce_ms", "0"))
                ),
                fmt_ms(fnum(r.get("idle_ms", "0"))),
            ]
            for r in rank_rows
        ],
    )

    body = [
        "# Final Demo Summary",
        "",
        f"- Run directory: `{run_dir}`",
        f"- Hostnames seen: {', '.join(f'`{h}`' for h in seen_hosts) if seen_hosts else '`none`'}",
        f"- Required hostnames: {', '.join(f'`{h}`' for h in args.require_host) if args.require_host else '`not enforced`'}",
        f"- Algorithm: `{correctness.get('algorithm', 'unknown')}`",
        f"- Processes: `{correctness.get('world_size', 'unknown')}`",
        f"- Runtime with communication: `{fmt_ms(fnum(correctness.get('total_ms_with_comm', '0')))}`",
        f"- Runtime without communication: `{fmt_ms(fnum(correctness.get('total_ms_without_comm', '0')))}`",
        f"- Max absolute error: `{fnum(correctness.get('max_abs_error', '0')):.6g}`",
        f"- Relative L2 error: `{fnum(correctness.get('relative_l2_error', '0')):.6g}`",
        "",
        "## Rank Work Breakdown",
        "",
        rank_table,
        "",
        "## Status",
        "",
    ]
    if errors:
        body.extend(f"- FAIL: {item}" for item in errors)
    else:
        body.append("- PASS: demo correctness and required host checks passed.")
    body.extend(f"- WARN: {item}" for item in warnings)
    body.append("")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(body), encoding="utf-8")

    status = "PASS" if not errors else "FAIL"
    print(f"DEMO_SUMMARY={output}")
    print(f"DEMO_SUMMARY_STATUS={status} FAIL={len(errors)} WARN={len(warnings)}")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
