from __future__ import annotations

import argparse
import os
import re
import shlex
import shutil
from pathlib import Path


VALID_ALGOS = {
    "mpi_online",
    "mpi_online_nb",
    "mpi_row",
    "mpi_row_nb",
}

VALID_ASSIGNMENTS = {"contiguous", "cyclic", "block_cyclic"}


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        try:
            parts = shlex.split(value)
            value = parts[0] if parts else ""
        except ValueError:
            value = value.strip("\"'")
        values[key] = value
    return values


def merged_config(path: Path) -> dict[str, str]:
    cfg = parse_env_file(path)
    for key, value in os.environ.items():
        if key.startswith("ATTN_") or key in {"MPI_LAN_CIDR", "MPI_MAP_BY"}:
            cfg[key] = value
    return cfg


def int_value(cfg: dict[str, str], key: str, default: int = 0) -> int:
    try:
        return int(str(cfg.get(key, default)).strip())
    except ValueError:
        return default


def int_list(cfg: dict[str, str], key: str) -> list[int]:
    out: list[int] = []
    for item in str(cfg.get(key, "")).split():
        try:
            out.append(int(item))
        except ValueError:
            pass
    return out


def add(rows: list[tuple[str, str, str]], status: str, item: str, detail: str) -> None:
    rows.append((status, item, detail))


def check_command(rows: list[tuple[str, str, str]], name: str, required: bool = True) -> None:
    path = shutil.which(name)
    if path:
        add(rows, "PASS", f"command {name}", path)
    else:
        add(rows, "FAIL" if required else "WARN", f"command {name}", "not found")


def check_file(rows: list[tuple[str, str, str]], path: Path, item: str, fail: bool = True) -> None:
    add(rows, "PASS" if path.exists() else ("FAIL" if fail else "WARN"), item, str(path))


def check_config_values(rows: list[tuple[str, str, str]], cfg: dict[str, str]) -> None:
    total = int_value(cfg, "ATTN_TOTAL_PROCS")
    add(rows, "PASS" if total > 0 else "FAIL", "ATTN_TOTAL_PROCS", str(total))

    p_list = int_list(cfg, "ATTN_P_LIST")
    if not p_list:
        add(rows, "FAIL", "ATTN_P_LIST", "empty")
    else:
        has_1 = 1 in p_list
        has_total = total in p_list
        status = "PASS" if has_1 and has_total else "WARN"
        add(rows, status, "ATTN_P_LIST", f"{p_list}, contains_1={has_1}, contains_total={has_total}")

    threads = int_value(cfg, "ATTN_THREADS")
    add(rows, "PASS" if threads == 1 else "WARN", "ATTN_THREADS", f"{threads}; required core-count experiments should use 1")

    algo = cfg.get("ATTN_ALGO", "")
    add(rows, "PASS" if algo in VALID_ALGOS else "FAIL", "ATTN_ALGO", algo)

    assignment = cfg.get("ATTN_ASSIGNMENT", "")
    add(rows, "PASS" if assignment in VALID_ASSIGNMENTS else "FAIL", "ATTN_ASSIGNMENT", assignment)

    find_n = int_list(cfg, "ATTN_FIND_N_LIST")
    add(rows, "PASS" if find_n else "FAIL", "ATTN_FIND_N_LIST", str(find_n))

    min_ms = int_value(cfg, "ATTN_TARGET_MIN_MS")
    max_ms = int_value(cfg, "ATTN_TARGET_MAX_MS")
    add(rows, "PASS" if 0 < min_ms < max_ms else "FAIL", "target runtime", f"min={min_ms}, max={max_ms}")

    evidence_np = int_value(cfg, "ATTN_EVIDENCE_NP")
    add(rows, "PASS" if evidence_np >= 3 else "WARN", "ATTN_EVIDENCE_NP", str(evidence_np))

    thread_np = int_value(cfg, "ATTN_THREAD_SWEEP_NP")
    add(rows, "PASS" if thread_np > 0 else "WARN", "ATTN_THREAD_SWEEP_NP", str(thread_np))

    thread_list = int_list(cfg, "ATTN_THREAD_LIST")
    add(rows, "PASS" if thread_list else "WARN", "ATTN_THREAD_LIST", str(thread_list))

    lan = cfg.get("MPI_LAN_CIDR", "")
    cidr_ok = bool(re.match(r"^\d+\.\d+\.\d+\.\d+/\d+$", lan))
    add(rows, "PASS" if cidr_ok else "WARN", "MPI_LAN_CIDR", lan or "missing")


def check_hostfile(rows: list[tuple[str, str, str]], cfg: dict[str, str]) -> None:
    use_hostfile = cfg.get("ATTN_USE_HOSTFILE", "1")
    hostfile = Path(cfg.get("ATTN_HOSTFILE", "configs/hosts"))
    if use_hostfile != "1":
        add(rows, "WARN", "hostfile mode", f"ATTN_USE_HOSTFILE={use_hostfile}")
        return
    check_file(rows, hostfile, "ATTN_HOSTFILE")
    if not hostfile.exists():
        return
    hosts = []
    for line in hostfile.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            hosts.append(line.split()[0])
    add(rows, "PASS" if len(set(hosts)) >= 3 else "WARN", "hostfile hosts", ", ".join(hosts))


def markdown(rows: list[tuple[str, str, str]]) -> str:
    out = [
        "# Experiment Config Preflight",
        "",
        "| status | item | detail |",
        "| --- | --- | --- |",
    ]
    for status, item, detail in rows:
        safe_detail = detail.replace("|", "\\|")
        out.append(f"| {status} | {item} | {safe_detail} |")
    out.append("")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/attention_experiment.env")
    parser.add_argument("--fallback-example", default="configs/attention_experiment.env.example")
    parser.add_argument("--output", default="")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    config = Path(args.config)
    fallback = Path(args.fallback_example)
    rows: list[tuple[str, str, str]] = []

    if config.exists():
        cfg_path = config
        add(rows, "PASS", "config file", str(config))
    else:
        cfg_path = fallback
        add(rows, "WARN", "config file", f"{config} missing; using {fallback}")

    cfg = merged_config(cfg_path)
    check_file(rows, Path("scripts/build.sh"), "build script")
    check_file(rows, Path("scripts/run_required_experiments.sh"), "final pipeline script")
    check_file(rows, Path(".venv-plot/bin/python"), "plot virtualenv", fail=False)
    check_command(rows, "git")
    check_command(rows, "bash")
    check_command(rows, "mpirun")
    check_command(rows, "mpicc")
    check_config_values(rows, cfg)
    check_hostfile(rows, cfg)

    text = markdown(rows)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"PREFLIGHT_REPORT={out}")

    fail = sum(1 for status, _, _ in rows if status == "FAIL")
    warn = sum(1 for status, _, _ in rows if status == "WARN")
    print(text)
    print(f"EXPERIMENT_PREFLIGHT_STATUS={'PASS' if fail == 0 else 'FAIL'} FAIL={fail} WARN={warn}")
    if fail > 0 or (args.strict and warn > 0):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
