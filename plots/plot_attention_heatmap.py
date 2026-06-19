from __future__ import annotations

import matplotlib.pyplot as plt

from plot_common import ensure_out, read_csv, require_cols


def plot(input_dir: str, output_dir: str) -> None:
    df = read_csv(input_dir, "attention_dump.csv")
    require_cols(df, ["i", "j", "p"], "attention_dump.csv")
    pivot = df.pivot_table(index="i", columns="j", values="p", aggfunc="mean").fillna(0)
    out = ensure_out(output_dir)
    plt.figure()
    plt.imshow(pivot.values, aspect="auto")
    plt.xlabel("key j")
    plt.ylabel("query i")
    plt.title("Attention heatmap")
    plt.colorbar(label="p")
    plt.tight_layout()
    plt.savefig(out / "09_attention_heatmap.png")
    plt.close()
