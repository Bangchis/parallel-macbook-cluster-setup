from __future__ import annotations

import matplotlib.pyplot as plt

from plot_common import ensure_out, read_csv, require_cols


def plot(input_dir: str, output_dir: str) -> None:
    df = read_csv(input_dir, "find_N.csv")
    require_cols(df, ["L", "total_ms_with_comm", "total_ms_without_comm"], "find_N.csv")
    out = ensure_out(output_dir)
    plt.figure()
    plt.plot(df["L"], df["total_ms_with_comm"], marker="o", label="with comm")
    plt.plot(df["L"], df["total_ms_without_comm"], marker="o", label="without comm")
    plt.xlabel("L")
    plt.ylabel("runtime ms")
    plt.title("Runtime vs sequence length")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out / "01_runtime_vs_L.png")
    plt.close()
