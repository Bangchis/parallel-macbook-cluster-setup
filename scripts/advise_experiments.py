from __future__ import annotations

import argparse
import csv
import math
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


def table(headers: list[str], rows: list[list[str]]) -> str:
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def round_multiple(value: float, step: int = 128) -> int:
    if value <= step:
        return step
    return max(step, int(round(value / step) * step))


def unique_sorted(values: list[int]) -> list[int]:
    return sorted({v for v in values if v > 0})


def estimate_l_for_target(rows: list[dict[str, str]], target_ms: float) -> int:
    valid = []
    for row in rows:
        L = inum(row.get("L", row.get("N", "0")))
        t = fnum(row.get("total_ms_with_comm", "0"))
        if L > 0 and t > 0:
            valid.append((L, t))
    if not valid:
        return 0

    # Attention is dominated by O(L^2). Use a least-squares coefficient for
    # t ~= c * L^2, robust enough for choosing the next benchmark candidates.
    num = sum((L * L) * t for L, t in valid)
    den = sum((L * L) ** 2 for L, _ in valid)
    if den <= 0:
        return 0
    c = num / den
    if c <= 0:
        return 0
    return round_multiple(math.sqrt(target_ms / c))


def selected_find_n(rows: list[dict[str, str]], min_ms: float, max_ms: float) -> dict[str, str] | None:
    if not rows:
        return None
    in_range = [
        row for row in rows
        if min_ms <= fnum(row.get("total_ms_with_comm", "0")) <= max_ms
    ]
    if in_range:
        return min(in_range, key=lambda r: inum(r.get("L", r.get("N", "0"))))
    target = (min_ms + max_ms) / 2.0
    return min(rows, key=lambda r: abs(fnum(r.get("total_ms_with_comm", "0")) - target))


def suggest_find_n(rows: list[dict[str, str]], min_ms: float, max_ms: float) -> tuple[str, str]:
    if not rows:
        body = "No `find_N.csv` rows found yet.\n"
        env = "# No find-N advice: missing find_N.csv\n"
        return body, env

    rows = sorted(rows, key=lambda r: inum(r.get("L", r.get("N", "0"))))
    chosen = selected_find_n(rows, min_ms, max_ms)
    target_mid = (min_ms + max_ms) / 2.0
    predicted_min = estimate_l_for_target(rows, min_ms)
    predicted_mid = estimate_l_for_target(rows, target_mid)
    predicted_max = estimate_l_for_target(rows, max_ms)
    measured_L = [inum(r.get("L", r.get("N", "0"))) for r in rows]
    candidates = unique_sorted(
        measured_L
        + [predicted_min, predicted_mid, predicted_max]
        + [round_multiple(predicted_mid * 0.75), round_multiple(predicted_mid * 1.25)]
    )

    chosen_runtime = fnum(chosen.get("total_ms_with_comm", "0")) if chosen else 0.0
    in_target = min_ms <= chosen_runtime <= max_ms
    selected_n = inum(chosen.get("L", chosen.get("N", "0"))) if chosen and in_target else 0
    selected_note = str(selected_n) if selected_n else "leave empty and rerun find-N"

    body = "\n".join([
        "## N Selection Advice",
        "",
        f"- Target runtime: `{fmt_ms(min_ms)}` to `{fmt_ms(max_ms)}`.",
        f"- Closest measured L: `{inum(chosen.get('L', chosen.get('N', '0')) if chosen else '0')}`.",
        f"- Closest measured runtime: `{fmt_ms(chosen_runtime)}`.",
        f"- Predicted L near target midpoint: `{predicted_mid or 'unknown'}`.",
        f"- Recommended `ATTN_FIND_N_LIST`: `{' '.join(str(x) for x in candidates)}`.",
        f"- Recommended `ATTN_SELECTED_N`: `{selected_note}`.",
        "",
        table(
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
        ),
        "",
    ])
    env = "\n".join([
        "# Suggested by scripts/advise_experiments.py from find_N.csv",
        f'export ATTN_FIND_N_LIST="{" ".join(str(x) for x in candidates)}"',
        f"export ATTN_SELECTED_N={selected_n if selected_n else ''}",
        "",
    ])
    return body, env


def suggest_granularity(rows: list[dict[str, str]]) -> tuple[str, str]:
    if not rows:
        body = "## Granularity Advice\n\nNo `granularity.csv` rows found yet.\n"
        env = "# No granularity advice: missing granularity.csv\n"
        return body, env

    acceptable = [r for r in rows if fnum(r.get("load_imbalance", "999")) <= 1.25]
    if acceptable:
        best = min(
            acceptable,
            key=lambda r: (
                fnum(r.get("total_ms_with_comm", "999999")),
                fnum(r.get("load_imbalance", "999")),
            ),
        )
        status = "acceptable"
        action = "Use the fastest configuration that is inside the 1.25 imbalance threshold."
    else:
        best = min(
            rows,
            key=lambda r: (
                fnum(r.get("load_imbalance", "999")),
                fnum(r.get("total_ms_with_comm", "999999")),
            ),
        )
        status = "needs another sweep"
        action = "Try finer block-cyclic granularity; include smaller `Br` values."

    best_assignment = best.get("assignment", "block_cyclic")
    best_br = max(1, inum(best.get("Br", "1")))
    observed_br = sorted({max(1, inum(r.get("Br", "1"))) for r in rows})
    br_candidates = unique_sorted([1, max(1, best_br // 4), max(1, best_br // 2), best_br, best_br * 2])
    if observed_br:
        br_candidates = unique_sorted(br_candidates + observed_br)

    body = "\n".join([
        "## Granularity Advice",
        "",
        f"- Balance status: `{status}`.",
        f"- Recommended assignment: `{best_assignment}`.",
        f"- Recommended Br: `{best_br}`.",
        f"- Best observed load imbalance: `{fnum(best.get('load_imbalance', '0')):.3f}`.",
        f"- Best observed runtime with communication: `{fmt_ms(fnum(best.get('total_ms_with_comm', '0')))}`.",
        f"- Next `ATTN_BR_LIST`: `{' '.join(str(x) for x in br_candidates)}`.",
        f"- Action: {action}",
        "",
        table(
            ["assignment", "Br", "runtime_with_comm", "runtime_without_comm", "imbalance"],
            [
                [
                    r.get("assignment", ""),
                    r.get("Br", ""),
                    fmt_ms(fnum(r.get("total_ms_with_comm", "0"))),
                    fmt_ms(fnum(r.get("total_ms_without_comm", "0"))),
                    f"{fnum(r.get('load_imbalance', '0')):.3f}",
                ]
                for r in sorted(rows, key=lambda r: (r.get("assignment", ""), inum(r.get("Br", "0"))))
            ],
        ),
        "",
    ])
    env = "\n".join([
        "# Suggested by scripts/advise_experiments.py from granularity.csv",
        f"export ATTN_ASSIGNMENT={best_assignment}",
        f"export ATTN_BR={best_br}",
        f'export ATTN_BR_LIST="{" ".join(str(x) for x in br_candidates)}"',
        "",
    ])
    return body, env


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/raw")
    parser.add_argument("--summary", default="")
    parser.add_argument("--output", default="results/tables/experiment_advisor.md")
    parser.add_argument("--env-output", default="")
    parser.add_argument("--min-ms", type=float, default=120000.0)
    parser.add_argument("--max-ms", type=float, default=180000.0)
    args = parser.parse_args()

    raw = Path(args.input)
    output = Path(args.output)
    env_output = Path(args.env_output) if args.env_output else output.with_suffix(".env")

    find_rows = read_rows(raw / "find_N.csv")
    gran_rows = read_rows(raw / "granularity.csv")
    find_body, find_env = suggest_find_n(find_rows, args.min_ms, args.max_ms)
    gran_body, gran_env = suggest_granularity(gran_rows)

    body = "\n".join([
        "# Experiment Advisor",
        "",
        "This file suggests the next benchmark settings from the measured CSV files.",
        "It is advisory only: inspect the recommendation before editing `configs/attention_experiment.env`.",
        "",
        find_body,
        gran_body,
    ])
    env = "\n".join([
        "# Experiment advisor suggestions.",
        "# Copy selected lines into configs/attention_experiment.env after review.",
        "",
        find_env,
        gran_env,
    ])

    output.parent.mkdir(parents=True, exist_ok=True)
    env_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(body, encoding="utf-8")
    env_output.write_text(env, encoding="utf-8")

    print(f"EXPERIMENT_ADVISOR={output}")
    print(f"EXPERIMENT_ADVISOR_ENV={env_output}")
    print("EXPERIMENT_ADVISOR_DONE=YES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
