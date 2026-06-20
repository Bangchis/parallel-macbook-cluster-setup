from __future__ import annotations

import argparse
import csv
import glob
from pathlib import Path


ASSIGNMENTS = [
    {
        "member": "Member 1",
        "role": "Tensor, serial baseline, correctness",
        "patterns": [
            "src/tensor.hpp",
            "src/tensor.cpp",
            "src/config.hpp",
            "src/config.cpp",
            "src/attention_serial.hpp",
            "src/attention_serial.cpp",
            "src/correctness.hpp",
            "src/correctness.cpp",
        ],
        "explain": [
            "Tensor4D index order",
            "stable softmax",
            "why serial attention is the correctness oracle",
            "max/mean/relative L2 error",
        ],
    },
    {
        "member": "Member 2",
        "role": "Online softmax, OpenMP, metrics",
        "patterns": [
            "src/attention_online.hpp",
            "src/attention_online.cpp",
            "src/attention_omp.hpp",
            "src/attention_omp.cpp",
            "src/metrics.hpp",
            "src/metrics.cpp",
        ],
        "explain": [
            "online softmax running max and denominator",
            "causal mask handling",
            "OpenMP scheduling",
            "thread-local buffers and no-lock row ownership",
        ],
    },
    {
        "member": "Member 3",
        "role": "MPI implementation and communication metrics",
        "patterns": [
            "src/attention_mpi.hpp",
            "src/attention_mpi.cpp",
            "src/csv_writer.hpp",
            "src/csv_writer.cpp",
            "src/main.cpp",
        ],
        "explain": [
            "MPI broadcast of Q/K/V",
            "row mapping strategies",
            "MPI reduce and gather steps",
            "communication versus compute timing",
        ],
    },
    {
        "member": "Member 4",
        "role": "Experiment pipeline, plots, docs, report artifacts",
        "patterns": [
            "scripts/*.sh",
            "scripts/*.py",
            "plots/*.py",
            "python_tests/*.py",
            "docs/attention/*.md",
            "README.md",
            "report/*.md",
        ],
        "explain": [
            "benchmark workflow",
            "find-N and speedup experiments",
            "rank breakdown and load-balance plots",
            "report and submission artifacts",
        ],
    },
]


def count_non_empty(path: Path) -> int:
    try:
        with path.open(encoding="utf-8", errors="ignore") as f:
            return sum(1 for line in f if line.strip())
    except OSError:
        return 0


def resolve_files(patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    seen: set[str] = set()
    for pattern in patterns:
        for item in glob.glob(pattern):
            path = Path(item)
            if path.is_file() and str(path) not in seen:
                files.append(path)
                seen.add(str(path))
    return sorted(files)


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/tables/member_contributions.md")
    parser.add_argument("--csv-output", default="")
    parser.add_argument("--threshold", type=int, default=250)
    args = parser.parse_args()

    output = Path(args.output)
    csv_output = Path(args.csv_output) if args.csv_output else output.with_suffix(".csv")

    rows: list[dict[str, str]] = []
    detail_sections: list[str] = []
    for assignment in ASSIGNMENTS:
        files = resolve_files(list(assignment["patterns"]))
        file_counts = [(path, count_non_empty(path)) for path in files]
        total = sum(count for _, count in file_counts)
        status = "PASS" if total >= args.threshold else "CHECK"
        rows.append(
            {
                "member": str(assignment["member"]),
                "role": str(assignment["role"]),
                "files": str(len(files)),
                "non_empty_lines": str(total),
                "threshold": str(args.threshold),
                "status": status,
            }
        )

        detail_sections.extend([
            f"## {assignment['member']}: {assignment['role']}",
            "",
            f"- Non-empty lines: `{total}`",
            f"- Status: `{status}` against threshold `{args.threshold}`",
            "- Must explain:",
            *(f"  - {item}" for item in assignment["explain"]),
            "",
            md_table(
                ["file", "non_empty_lines"],
                [[f"`{path}`", str(count)] for path, count in file_counts],
            ),
            "",
        ])

    summary = md_table(
        ["member", "role", "files", "non_empty_lines", "status"],
        [
            [
                row["member"],
                row["role"],
                row["files"],
                row["non_empty_lines"],
                row["status"],
            ]
            for row in rows
        ],
    )

    body = "\n".join([
        "# Member Contribution Evidence",
        "",
        "This report maps the project codebase to the four-member ownership plan.",
        "It is not a fake Git authorship claim; it is an explainable module ownership map for the final demo.",
        "",
        summary,
        "",
        *detail_sections,
    ])

    output.parent.mkdir(parents=True, exist_ok=True)
    csv_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(body, encoding="utf-8")
    with csv_output.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["member", "role", "files", "non_empty_lines", "threshold", "status"],
        )
        writer.writeheader()
        writer.writerows(rows)

    fail = sum(1 for row in rows if row["status"] != "PASS")
    print(f"MEMBER_CONTRIBUTIONS={output}")
    print(f"MEMBER_CONTRIBUTIONS_CSV={csv_output}")
    print(f"MEMBER_CONTRIBUTIONS_STATUS={'PASS' if fail == 0 else 'CHECK'} FAIL={fail}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
