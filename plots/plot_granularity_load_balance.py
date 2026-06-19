from __future__ import annotations

import matplotlib.pyplot as plt

from plot_common import ensure_out, read_csv, require_cols


def plot(input_dir: str, output_dir: str) -> None:
    df = read_csv(input_dir, "granularity.csv")
    require_cols(df, ["Br", "assignment", "load_imbalance", "total_ms_without_comm"], "granularity.csv")
    out = ensure_out(output_dir)
    plt.figure()
    for assignment, group in df.groupby("assignment"):
        group = group.sort_values("Br")
        plt.plot(group["Br"], group["load_imbalance"], marker="o", label=assignment)
    plt.axhline(1.25, linestyle="--", color="red", label="25% imbalance")
    plt.xlabel("Br")
    plt.ylabel("load imbalance")
    plt.title("Granularity and load balancing")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out / "06_granularity_load_balance.png")
    plt.close()
