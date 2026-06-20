from __future__ import annotations

import matplotlib.pyplot as plt

from plot_common import ensure_out, read_csv, require_cols


def plot(input_dir: str, output_dir: str) -> None:
    df = read_csv(input_dir, "comm_strategy.csv")
    require_cols(
        df,
        ["algorithm", "world_size", "compute_ms_max", "comm_ms_total", "total_ms_with_comm"],
        "comm_strategy.csv",
    )
    df = df.sort_values(["world_size", "algorithm"])
    labels = [f"{row.algorithm}\nP={int(row.world_size)}" for row in df.itertuples()]
    out = ensure_out(output_dir)
    plt.figure()
    plt.bar(labels, df["compute_ms_max"], label="compute")
    plt.bar(labels, df["comm_ms_total"], bottom=df["compute_ms_max"], label="communication")
    plt.ylabel("time ms")
    plt.title("Blocking vs non-blocking MPI communication")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out / "10_comm_strategy.png")
    plt.close()
