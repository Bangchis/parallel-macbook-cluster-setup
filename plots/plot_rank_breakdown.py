from __future__ import annotations

import matplotlib.pyplot as plt

from plot_common import ensure_out, read_csv, require_cols


def plot(input_dir: str, output_dir: str) -> None:
    df = read_csv(input_dir, "rank_metrics.csv")
    require_cols(df, ["rank", "compute_ms", "bcast_ms", "gather_ms", "reduce_ms"], "rank_metrics.csv")
    latest = df[df["run_id"] == df.iloc[-1]["run_id"]]
    out = ensure_out(output_dir)
    plt.figure()
    x = latest["rank"].astype(str)
    bottom = latest["compute_ms"] * 0
    for col in ["compute_ms", "bcast_ms", "gather_ms", "reduce_ms"]:
        plt.bar(x, latest[col], bottom=bottom, label=col)
        bottom = bottom + latest[col]
    plt.xlabel("rank")
    plt.ylabel("time ms")
    plt.title("Per-rank time breakdown")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out / "05_rank_breakdown.png")
    plt.close()
