from __future__ import annotations

from pathlib import Path

import pandas as pd


def read_csv(input_dir: str, name: str) -> pd.DataFrame:
    path = Path(input_dir) / name
    if not path.exists():
        raise FileNotFoundError(f"Missing CSV: {path}")
    return pd.read_csv(path)


def require_cols(df: pd.DataFrame, cols: list[str], source: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{source} missing columns: {missing}")


def ensure_out(output_dir: str) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    return out
