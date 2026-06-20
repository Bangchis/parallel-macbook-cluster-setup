from __future__ import annotations

import matplotlib.pyplot as plt

from plot_common import ensure_out, read_csv, require_cols


def plot(input_dir: str, output_dir: str) -> None:
    df = read_csv(input_dir, "thread_scaling.csv")
    require_cols(df, ["omp_threads", "total_ms_with_comm", "total_ms_without_comm"], "thread_scaling.csv")
    df = df.sort_values("omp_threads")
    out = ensure_out(output_dir)
    plt.figure()
    plt.plot(df["omp_threads"], df["total_ms_with_comm"], marker="o", label="with comm")
    plt.plot(df["omp_threads"], df["total_ms_without_comm"], marker="o", label="without comm")
    plt.xlabel("OpenMP threads per rank")
    plt.ylabel("runtime ms")
    plt.title("OpenMP thread scaling")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out / "11_thread_scaling.png")
    plt.close()
