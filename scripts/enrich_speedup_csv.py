from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


GROUP_COLS = [
    "algorithm",
    "B",
    "H",
    "L",
    "Dh",
    "N",
    "Br",
    "Bc",
    "causal",
    "assignment",
    "schedule",
    "omp_threads",
]

DERIVED_COLS = [
    "speedup_with_comm",
    "speedup_without_comm",
    "efficiency_with_comm",
    "efficiency_without_comm",
]


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
    return f"{value:.8g}"


def group_key(row: dict[str, str]) -> tuple[str, ...]:
    return tuple(row.get(col, "") for col in GROUP_COLS)


def baseline_row(rows: list[dict[str, str]]) -> dict[str, str]:
    p1 = [r for r in rows if inum(r.get("world_size", "0")) == 1]
    if p1:
        return p1[0]
    return min(rows, key=lambda r: max(1, inum(r.get("world_size", "1"))))


def enrich(rows: list[dict[str, str]]) -> int:
    groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[group_key(row)].append(row)

    updated = 0
    for group_rows in groups.values():
        base = baseline_row(group_rows)
        base_p = max(1, inum(base.get("world_size", "1")))
        base_comm = fnum(base.get("total_ms_with_comm", "0"))
        base_no = fnum(base.get("total_ms_without_comm", "0"))

        for row in group_rows:
            p = max(1, inum(row.get("world_size", "1")))
            t_comm = fnum(row.get("total_ms_with_comm", "0"))
            t_no = fnum(row.get("total_ms_without_comm", "0"))
            s_comm = base_comm / t_comm if base_comm > 0 and t_comm > 0 else 0.0
            s_no = base_no / t_no if base_no > 0 and t_no > 0 else 0.0

            # If the baseline is not P=1, normalize to the measured baseline
            # process count. Final runs should include P=1, but this keeps
            # small smoke runs readable.
            effective_p = p / base_p
            eff_comm = s_comm / effective_p if effective_p > 0 else 0.0
            eff_no = s_no / effective_p if effective_p > 0 else 0.0

            new_values = {
                "speedup_with_comm": fmt(s_comm),
                "speedup_without_comm": fmt(s_no),
                "efficiency_with_comm": fmt(eff_comm),
                "efficiency_without_comm": fmt(eff_no),
            }
            for key, value in new_values.items():
                if row.get(key, "") != value:
                    row[key] = value
                    updated += 1
    return updated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/raw/speedup.csv")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.exists():
        print(f"SPEEDUP_ENRICH_SKIP=missing {src}")
        return 0

    with src.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    for col in DERIVED_COLS:
        if col not in fieldnames:
            fieldnames.append(col)

    updated = enrich(rows)
    out = Path(args.output) if args.output else src
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"SPEEDUP_ENRICHED={out}")
    print(f"SPEEDUP_ROWS={len(rows)} UPDATED_FIELDS={updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
