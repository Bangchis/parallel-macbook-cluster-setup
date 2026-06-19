from __future__ import annotations

import matplotlib.pyplot as plt

from plot_common import ensure_out, read_csv, require_cols


def plot(input_dir: str, output_dir: str) -> None:
    df = read_csv(input_dir, "speedup.csv")
    require_cols(df, ["world_size", "total_ms_with_comm", "total_ms_without_comm"], "speedup.csv")
    df = df.sort_values("world_size")
    out = ensure_out(output_dir)
    plt.figure()
    plt.plot(df["world_size"], df["total_ms_with_comm"], marker="o", label="with comm")
    plt.plot(df["world_size"], df["total_ms_without_comm"], marker="o", label="without comm")
    plt.xlabel("processes")
    plt.ylabel("runtime ms")
    plt.title("Runtime with and without communication")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out / "02_runtime_with_without_comm.png")
    plt.close()
