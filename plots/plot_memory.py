from __future__ import annotations

import matplotlib.pyplot as plt

from plot_common import ensure_out, read_csv, require_cols


def plot(input_dir: str, output_dir: str) -> None:
    df = read_csv(input_dir, "summary.csv")
    require_cols(df, ["algorithm", "memory_estimated_mb"], "summary.csv")
    latest = df.tail(min(8, len(df)))
    out = ensure_out(output_dir)
    plt.figure()
    plt.bar(latest["algorithm"], latest["memory_estimated_mb"])
    plt.xlabel("algorithm")
    plt.ylabel("estimated MB")
    plt.title("Memory estimate")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(out / "07_memory_comparison.png")
    plt.close()
