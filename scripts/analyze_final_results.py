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


def inum(value: str, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def fmt_ms(value: float) -> str:
    if value >= 1000.0:
        return f"{value / 1000.0:.2f}s"
    return f"{value:.3f}ms"


def parse_summary(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def table(headers: list[str], rows: list[list[str]]) -> str:
    out = []
    out.append("| " + " | ".join(headers) + " |")
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def section_find_n(raw: Path, summary: dict[str, str]) -> str:
    rows = read_rows(raw / "find_N.csv")
    if not rows:
        return "## Find N\n\nNo `find_N.csv` data found.\n"

    selected = summary.get("ATTN_SELECTED_N", "")
    target_min = fnum(summary.get("ATTN_TARGET_MIN_MS", "120000"))
    target_max = fnum(summary.get("ATTN_TARGET_MAX_MS", "180000"))
    closest = min(rows, key=lambda r: abs(fnum(r.get("total_ms_with_comm", "0")) - (target_min + target_max) / 2.0))
    in_range = [
        r for r in rows
        if target_min <= fnum(r.get("total_ms_with_comm", "0")) <= target_max
    ]
    chosen = next((r for r in rows if r.get("L", r.get("N", "")) == selected), None)
    if chosen is None:
        chosen = in_range[0] if in_range else closest

    body = [
        "## Find N",
        "",
        f"- Target runtime: `{fmt_ms(target_min)}` to `{fmt_ms(target_max)}`.",
        f"- Selected N: `{chosen.get('L', chosen.get('N', 'unknown'))}`.",
        f"- Selected runtime with communication: `{fmt_ms(fnum(chosen.get('total_ms_with_comm', '0')))}`.",
    ]
    if not in_range:
        body.append("- Note: no candidate reached the target range; expand `ATTN_FIND_N_LIST` for the final cluster run.")
    body.append("")
    body.append(table(
        ["L", "P", "runtime_with_comm", "runtime_without_comm"],
        [
            [
                r.get("L", r.get("N", "")),
                r.get("world_size", ""),
                fmt_ms(fnum(r.get("total_ms_with_comm", "0"))),
                fmt_ms(fnum(r.get("total_ms_without_comm", "0"))),
            ]
            for r in rows
        ],
    ))
    body.append("")
    return "\n".join(body)


def section_speedup(raw: Path) -> str:
    rows = read_rows(raw / "speedup.csv")
    if not rows:
        return "## Speedup\n\nNo `speedup.csv` data found.\n"
    rows = sorted(rows, key=lambda r: inum(r.get("world_size", "0")))
    base_comm = fnum(rows[0].get("total_ms_with_comm", "0"))
    base_no = fnum(rows[0].get("total_ms_without_comm", "0"))
    last = rows[-1]
    p_last = max(1, inum(last.get("world_size", "1")))
    s_comm = base_comm / fnum(last.get("total_ms_with_comm", "1"), 1.0)
    s_no = base_no / fnum(last.get("total_ms_without_comm", "1"), 1.0)

    body = [
        "## Speedup",
        "",
        f"- Largest tested process count: `{p_last}`.",
        f"- Speedup with communication at largest P: `{s_comm:.3f}`.",
        f"- Speedup without communication at largest P: `{s_no:.3f}`.",
        f"- Efficiency with communication at largest P: `{s_comm / p_last:.3f}`.",
        "",
        table(
            ["P", "speedup_with_comm", "speedup_without_comm", "eff_with_comm"],
            [
                [
                    r.get("world_size", ""),
                    f"{base_comm / fnum(r.get('total_ms_with_comm', '1'), 1.0):.3f}",
                    f"{base_no / fnum(r.get('total_ms_without_comm', '1'), 1.0):.3f}",
                    f"{(base_comm / fnum(r.get('total_ms_with_comm', '1'), 1.0)) / max(1, inum(r.get('world_size', '1'))):.3f}",
                ]
                for r in rows
            ],
        ),
        "",
    ]
    return "\n".join(body)


def section_granularity(raw: Path) -> str:
    rows = read_rows(raw / "granularity.csv")
    if not rows:
        return "## Granularity And Load Balance\n\nNo `granularity.csv` data found.\n"
    acceptable = [r for r in rows if fnum(r.get("load_imbalance", "999")) <= 1.25]
    candidates = acceptable if acceptable else rows
    best = min(
        candidates,
        key=lambda r: (
            fnum(r.get("load_imbalance", "999")),
            fnum(r.get("total_ms_without_comm", "999999")),
        ),
    )
    status = "acceptable" if acceptable else "needs adjustment"
    body = [
        "## Granularity And Load Balance",
        "",
        f"- Best observed mapping: `{best.get('assignment', '')}`.",
        f"- Best observed Br: `{best.get('Br', '')}`.",
        f"- Best observed load imbalance: `{fnum(best.get('load_imbalance', '0')):.3f}`.",
        f"- Balance status: `{status}` against the 1.25 threshold.",
        "",
    ]
    if not acceptable:
        body.append("- Recommendation: try smaller `Br` values or include more `block_cyclic` candidates in `ATTN_BR_LIST`.")
        body.append("")
    return "\n".join(body)


def section_blocksize(raw: Path) -> str:
    rows = read_rows(raw / "blocksize.csv")
    if not rows:
        return "## Block Size\n\nNo `blocksize.csv` data found.\n"
    best = min(rows, key=lambda r: fnum(r.get("total_ms_without_comm", "999999")))
    return "\n".join([
        "## Block Size",
        "",
        f"- Fastest observed Br: `{best.get('Br', '')}`.",
        f"- Fastest observed Bc: `{best.get('Bc', '')}`.",
        f"- Runtime without communication: `{fmt_ms(fnum(best.get('total_ms_without_comm', '0')))}`.",
        "",
    ])


def section_comm(raw: Path) -> str:
    rows = read_rows(raw / "comm_strategy.csv")
    if not rows:
        return "## Communication Strategy\n\nNo `comm_strategy.csv` data found.\n"
    best = min(rows, key=lambda r: fnum(r.get("total_ms_with_comm", "999999")))
    body = [
        "## Communication Strategy",
        "",
        f"- Fastest communication strategy in this run: `{best.get('algorithm', '')}`.",
        f"- Total time: `{fmt_ms(fnum(best.get('total_ms_with_comm', '0')))}`.",
        f"- Communication time: `{fmt_ms(fnum(best.get('comm_ms_total', '0')))}`.",
        "",
        table(
            ["algorithm", "total", "compute", "communication"],
            [
                [
                    r.get("algorithm", ""),
                    fmt_ms(fnum(r.get("total_ms_with_comm", "0"))),
                    fmt_ms(fnum(r.get("compute_ms_max", "0"))),
                    fmt_ms(fnum(r.get("comm_ms_total", "0"))),
                ]
                for r in rows
            ],
        ),
        "",
    ]
    return "\n".join(body)


def section_hosts(raw: Path) -> str:
    rows = read_rows(raw / "rank_metrics.csv")
    hosts = sorted({r.get("hostname", "") for r in rows if r.get("hostname", "")})
    return "\n".join([
        "## Cluster Evidence",
        "",
        "- Hostnames seen in rank metrics: " + (", ".join(f"`{h}`" for h in hosts) if hosts else "`none`"),
        "- Final cluster run should include `master`, `node1`, and `node2`.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/raw")
    parser.add_argument("--summary", default="")
    parser.add_argument("--output", default="results/tables/analysis.md")
    args = parser.parse_args()

    raw = Path(args.input)
    summary_path = Path(args.summary) if args.summary else raw.parent / "experiment_summary.env"
    summary = parse_summary(summary_path)

    parts = [
        "# Final Results Analysis",
        "",
        section_hosts(raw),
        section_find_n(raw, summary),
        section_speedup(raw),
        section_granularity(raw),
        section_blocksize(raw),
        section_comm(raw),
    ]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(parts), encoding="utf-8")
    print(f"ANALYSIS_OK={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
