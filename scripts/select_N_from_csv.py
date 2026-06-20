from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/raw/find_N.csv")
    parser.add_argument("--min-ms", type=float, default=120000.0)
    parser.add_argument("--max-ms", type=float, default=180000.0)
    parser.add_argument("--algorithm", default="")
    parser.add_argument("--world-size", type=int, default=0)
    parser.add_argument("--explain", action="store_true")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"ERROR: missing {path}", file=sys.stderr)
        return 1

    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))

    filtered = []
    for row in rows:
        if args.algorithm and row.get("algorithm", "") != args.algorithm:
            continue
        if args.world_size and inum(row.get("world_size", "0")) != args.world_size:
            continue
        filtered.append(row)

    if not filtered:
        print("ERROR: no matching rows in find_N.csv", file=sys.stderr)
        return 1

    target_mid = (args.min_ms + args.max_ms) / 2.0

    def runtime(row: dict[str, str]) -> float:
        return fnum(row.get("total_ms_with_comm", "0"))

    in_range = [row for row in filtered if args.min_ms <= runtime(row) <= args.max_ms]
    if in_range:
        chosen = sorted(in_range, key=lambda r: inum(r.get("L", r.get("N", "0"))))[0]
        reason = "inside_target_range"
    else:
        chosen = min(filtered, key=lambda r: abs(runtime(r) - target_mid))
        reason = "closest_to_target_midpoint"

    selected_n = inum(chosen.get("L", chosen.get("N", "0")))
    if args.explain:
        print(
            "SELECT_N "
            f"N={selected_n} "
            f"runtime_ms={runtime(chosen):.3f} "
            f"target_min_ms={args.min_ms:.3f} "
            f"target_max_ms={args.max_ms:.3f} "
            f"reason={reason}",
            file=sys.stderr,
        )

    print(selected_n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
