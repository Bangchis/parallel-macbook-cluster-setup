from __future__ import annotations

import matplotlib.pyplot as plt

from plot_common import ensure_out, read_csv, require_cols


def plot(input_dir: str, output_dir: str) -> None:
    df = read_csv(input_dir, "speedup.csv")
    require_cols(df, ["world_size", "total_ms_with_comm", "total_ms_without_comm"], "speedup.csv")
    df = df.sort_values("world_size")
    t1_comm = float(df.iloc[0]["total_ms_with_comm"])
    t1_no = float(df.iloc[0]["total_ms_without_comm"])
    speed_comm = t1_comm / df["total_ms_with_comm"]
    speed_no = t1_no / df["total_ms_without_comm"]
    out = ensure_out(output_dir)
    plt.figure()
    plt.plot(df["world_size"], speed_comm / df["world_size"], marker="o", label="with comm")
    plt.plot(df["world_size"], speed_no / df["world_size"], marker="o", label="without comm")
    plt.xlabel("processes")
    plt.ylabel("efficiency")
    plt.title("Efficiency")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out / "04_efficiency.png")
    plt.close()
