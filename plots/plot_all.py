from __future__ import annotations

import argparse
import importlib

def try_plot(module_name: str, label: str, input_dir: str, output_dir: str) -> None:
    try:
        module = importlib.import_module(module_name)
        module.plot(input_dir, output_dir)
        print(f"{label}: OK")
    except Exception as e:
        print(f"{label}: SKIP ({e})")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/raw")
    parser.add_argument("--output", default="results/figures")
    args = parser.parse_args()

    try_plot("plot_runtime_vs_L", "runtime_vs_L", args.input, args.output)
    try_plot("plot_runtime_with_without_comm", "runtime_with_without_comm", args.input, args.output)
    try_plot("plot_speedup", "speedup", args.input, args.output)
    try_plot("plot_efficiency", "efficiency", args.input, args.output)
    try_plot("plot_rank_breakdown", "rank_breakdown", args.input, args.output)
    try_plot("plot_granularity_load_balance", "granularity_load_balance", args.input, args.output)
    try_plot("plot_memory", "memory", args.input, args.output)
    try_plot("plot_blocksize_heatmap", "blocksize_heatmap", args.input, args.output)
    try_plot("plot_attention_heatmap", "attention_heatmap", args.input, args.output)
    try_plot("plot_comm_strategy", "comm_strategy", args.input, args.output)
    print("PLOT_ALL_DONE=YES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
