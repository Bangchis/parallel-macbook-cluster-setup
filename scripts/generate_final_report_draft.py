from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path


FIGURES = [
    ("01_runtime_vs_L.png", "Runtime versus input size L"),
    ("02_runtime_with_without_comm.png", "Runtime with and without communication"),
    ("03_speedup.png", "Speedup"),
    ("04_efficiency.png", "Parallel efficiency"),
    ("05_rank_breakdown.png", "Per-rank compute and communication breakdown"),
    ("06_granularity_load_balance.png", "Granularity and load balance"),
    ("07_memory_comparison.png", "Memory comparison"),
    ("08_blocksize_heatmap.png", "Block-size sweep"),
    ("09_attention_heatmap.png", "Attention probability heatmap"),
    ("10_comm_strategy.png", "Blocking versus non-blocking communication"),
    ("11_thread_scaling.png", "OpenMP thread scaling"),
]

TABLES = [
    ("correctness.md", "Correctness"),
    ("speedup.md", "Speedup and efficiency"),
    ("granularity.md", "Granularity and load balance"),
    ("rank_breakdown.md", "Rank breakdown"),
    ("communication.md", "Communication strategy"),
    ("thread_scaling.md", "OpenMP thread scaling"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore").strip()


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


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


def rel(path: Path, start: Path) -> str:
    return os.path.relpath(path, start=start)


def table(headers: list[str], rows: list[list[str]]) -> str:
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def one_line_table(title: str, values: list[tuple[str, str]]) -> str:
    return "\n".join([
        f"### {title}",
        "",
        table(["item", "value"], [[k, v] for k, v in values]),
        "",
    ])


def section_figures(run_dir: Path, out_dir: Path) -> str:
    parts = ["## Figures", ""]
    for filename, caption in FIGURES:
        path = run_dir / "figures" / filename
        if path.exists():
            parts.append(f"![{caption}]({rel(path, out_dir)})")
            parts.append("")
            parts.append(f"Figure: {caption}.")
            parts.append("")
        else:
            parts.append(f"- Missing figure: `{filename}`")
    return "\n".join(parts)


def section_tables(run_dir: Path) -> str:
    parts = ["## Result Tables", ""]
    for filename, title in TABLES:
        text = read_text(run_dir / "tables" / filename)
        if text:
            parts.append(f"### {title}")
            parts.append("")
            lines = text.splitlines()
            if lines and lines[0].startswith("# "):
                lines = lines[2:] if len(lines) > 1 and not lines[1].strip() else lines[1:]
            parts.append("\n".join(lines).strip())
            parts.append("")
        else:
            parts.append(f"- Missing table: `{filename}`")
    return "\n".join(parts)


def section_experiment_summary(run_dir: Path) -> str:
    values = parse_env(run_dir / "experiment_summary.env")
    raw = run_dir / "raw"
    speed_rows = read_csv(raw / "speedup.csv")
    gran_rows = read_csv(raw / "granularity.csv")
    demo_rows = read_csv(raw / "demo_correctness.csv")
    rank_rows = read_csv(raw / "rank_metrics.csv")

    hosts = sorted({r.get("hostname", "") for r in rank_rows if r.get("hostname", "")})
    best_gran = min(
        gran_rows,
        key=lambda r: (fnum(r.get("load_imbalance", "999")), fnum(r.get("total_ms_without_comm", "999999"))),
        default={},
    )

    speed_rows = sorted(speed_rows, key=lambda r: inum(r.get("world_size", "0")))
    if speed_rows:
        base = fnum(speed_rows[0].get("total_ms_with_comm", "0"))
        last = speed_rows[-1]
        last_p = max(1, inum(last.get("world_size", "1")))
        speedup = base / fnum(last.get("total_ms_with_comm", "1"), 1.0)
    else:
        last_p = 0
        speedup = 0.0

    demo = demo_rows[-1] if demo_rows else {}
    return one_line_table(
        "Final Run Summary",
        [
            ("run directory", f"`{run_dir}`"),
            ("cluster hostnames seen", ", ".join(f"`{h}`" for h in hosts) if hosts else "`none`"),
            ("selected N", f"`{values.get('ATTN_SELECTED_N', 'unknown')}`"),
            ("speedup input 2N", f"`{values.get('ATTN_SPEEDUP_L', 'unknown')}`"),
            ("total process target", f"`{values.get('ATTN_TOTAL_PROCS', 'unknown')}`"),
            ("largest P in speedup test", f"`{last_p}`"),
            ("speedup with communication at largest P", f"`{speedup:.3f}`"),
            ("best load imbalance", f"`{fnum(best_gran.get('load_imbalance', '0')):.3f}`"),
            ("best assignment", f"`{best_gran.get('assignment', 'unknown')}`"),
            ("best Br", f"`{best_gran.get('Br', 'unknown')}`"),
            ("correctness max abs error", f"`{fnum(demo.get('max_abs_error', '0')):.6g}`"),
            ("correctness relative L2 error", f"`{fnum(demo.get('relative_l2_error', '0')):.6g}`"),
        ],
    )


def section_analysis(run_dir: Path) -> str:
    analysis = read_text(run_dir / "tables" / "analysis.md")
    if not analysis:
        return "## Generated Analysis\n\nNo generated `analysis.md` found yet.\n"
    return "\n".join([
        "## Generated Analysis",
        "",
        analysis,
        "",
    ])


def section_evidence(run_dir: Path) -> str:
    evidence = run_dir / "evidence" / "cluster_evidence.txt"
    hosts_used = run_dir / "evidence" / "hosts.used"
    readiness = run_dir / "readiness.md"
    lines = [
        "## Cluster Evidence",
        "",
        "The final run must prove that MPI ranks executed on three physical machines.",
        "",
        "- Cluster evidence log: " + (f"`{evidence}`" if evidence.exists() else "`missing`"),
        "- Hostfile copy: " + (f"`{hosts_used}`" if hosts_used.exists() else "`missing`"),
        "- Readiness report: " + (f"`{readiness}`" if readiness.exists() else "`missing`"),
        "",
    ]
    if evidence.exists():
        text = evidence.read_text(encoding="utf-8", errors="ignore")
        important = []
        for line in text.splitlines():
            if (
                "COMMAND:" in line
                or "EVIDENCE_DONE" in line
                or line.strip() in {"master", "node1", "node2"}
            ):
                important.append(line)
        if important:
            lines.extend(["Important evidence lines:", "", "```text"])
            lines.extend(important[:40])
            lines.extend(["```", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--output", default="")
    parser.add_argument("--members", default="Member 1, Member 2, Member 3, Member 4")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    output = Path(args.output) if args.output else run_dir / "report" / "final_report_draft.md"
    out_dir = output.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    members = [m.strip() for m in args.members.split(",") if m.strip()]
    while len(members) < 4:
        members.append(f"Member {len(members) + 1}")

    parts = [
        "# Hybrid MPI + OpenMP Blocked Online Self-Attention",
        "",
        "Course: Parallel and Distributed Programming",
        "",
        "Group members:",
        "",
        *(f"- {member}" for member in members[:4]),
        "",
        "## Abstract",
        "",
        "This project implements the self-attention inference kernel "
        "`O = softmax(QK^T / sqrt(Dh)) V` on a three-machine OpenMPI cluster. "
        "The implementation compares a serial baseline, OpenMP versions, MPI "
        "versions, and hybrid MPI + OpenMP blocked online attention. The main "
        "parallelism is data-level parallelism over query rows, with OpenMP "
        "threads splitting local row work inside each MPI rank.",
        "",
        "## Problem And Serial Baseline",
        "",
        "Input tensors have shape `B x H x L x Dh`, where `B` is batch size, "
        "`H` is number of heads, `L` is sequence length, and `Dh` is the head "
        "dimension. For each query row, the serial algorithm computes dot "
        "products against all keys, applies a numerically stable softmax, and "
        "multiplies the probabilities by `V`.",
        "",
        "The time complexity is `O(B * H * L^2 * Dh)`. A naive full attention "
        "matrix uses `O(B * H * L^2)` memory, so the project also implements "
        "row-wise and blocked online softmax variants that avoid materializing "
        "the full score matrix.",
        "",
        "## Blocked Online Softmax",
        "",
        "The online algorithm scans key/value rows in blocks of size `Bc`. For "
        "each query row it keeps a running maximum `m`, denominator `l`, and "
        "output vector accumulator. When a later block contains a larger score, "
        "the previous denominator and output are rescaled before adding the "
        "new block. This preserves the same mathematical result as ordinary "
        "softmax while reducing memory usage.",
        "",
        "## Parallel Design",
        "",
        "- Parallel level: data-level parallelism over query rows.",
        "- Decomposition: one-dimensional row decomposition of global query rows.",
        "- Mapping: contiguous, cyclic, and block-cyclic assignment.",
        "- Main mapping: `owner_rank = (global_row / Br) % world_size`.",
        "- Communication: rank 0 broadcasts `Q`, `K`, and `V`; ranks reduce the "
        "partial output and checksum; metrics are gathered to rank 0.",
        "- Communication comparison: blocking `MPI_Bcast`/`MPI_Reduce` versus "
        "non-blocking `MPI_Ibcast`/`MPI_Ireduce`.",
        "- Load balancing metric: `max_rank_compute_ms / avg_rank_compute_ms`, "
        "with target threshold `<= 1.25`.",
        "",
        "## Parallel Pseudocode",
        "",
        "```text",
        "rank 0 generates Q, K, V",
        "MPI broadcasts Q, K, V to every rank",
        "for each MPI rank r:",
        "  OpenMP parallel for over all global query rows",
        "  if row belongs to rank r under the selected mapping:",
        "    compute blocked online attention for that row",
        "    write row into the local output tensor",
        "MPI reduces local output tensors into the final output on rank 0",
        "MPI reduces checksums and gathers timing metrics",
        "rank 0 compares the parallel output with the serial baseline",
        "rank 0 writes CSV metrics, plots, and report tables",
        "```",
        "",
        section_experiment_summary(run_dir),
        section_evidence(run_dir),
        "## Correctness Method",
        "",
        "Correctness is checked by comparing the selected parallel output with "
        "the serial row-wise attention baseline on deterministic random inputs. "
        "The report uses maximum absolute error, mean absolute error, and "
        "relative L2 error. A run is accepted when the errors are below the "
        "tolerance used by the benchmark checker.",
        "",
        section_tables(run_dir),
        section_figures(run_dir, out_dir),
        section_analysis(run_dir),
        "## Member Contributions",
        "",
        f"- {members[0]}: tensor representation, config parsing, serial baseline, correctness checks.",
        f"- {members[1]}: blocked online softmax, OpenMP implementation, timing metrics.",
        f"- {members[2]}: MPI row decomposition, communication variants, rank/thread metrics.",
        f"- {members[3]}: experiment scripts, plots, report artifacts, cluster/demo workflow.",
        "",
        "Each member should review the files listed in `docs/attention/04_MEMBER_TASKS.md` "
        "and be able to explain the corresponding code during the demo.",
        "",
        "## Conclusion",
        "",
        "The project demonstrates a meaningful hybrid MPI + OpenMP implementation "
        "of an AI inference kernel on a three-machine physical cluster. The "
        "main expected limitations are communication overhead, synchronization "
        "costs, and load imbalance when row granularity is poorly chosen. The "
        "blocked online softmax version improves memory behavior while keeping "
        "correctness equivalent to the serial baseline.",
        "",
    ]

    output.write_text("\n".join(parts), encoding="utf-8")
    print(f"FINAL_REPORT_DRAFT={output}")
    print("FINAL_REPORT_DRAFT_DONE=YES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
