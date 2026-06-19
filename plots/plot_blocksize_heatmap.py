from __future__ import annotations

import matplotlib.pyplot as plt

from plot_common import ensure_out, read_csv, require_cols


def plot(input_dir: str, output_dir: str) -> None:
    df = read_csv(input_dir, "blocksize.csv")
    require_cols(df, ["Br", "Bc", "total_ms_without_comm"], "blocksize.csv")
    pivot = df.pivot_table(index="Br", columns="Bc", values="total_ms_without_comm", aggfunc="mean")
    out = ensure_out(output_dir)
    plt.figure()
    plt.imshow(pivot.values, aspect="auto")
    plt.xticks(range(len(pivot.columns)), pivot.columns)
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.xlabel("Bc")
    plt.ylabel("Br")
    plt.title("Block-size runtime heatmap")
    plt.colorbar(label="runtime ms")
    plt.tight_layout()
    plt.savefig(out / "08_blocksize_heatmap.png")
    plt.close()
