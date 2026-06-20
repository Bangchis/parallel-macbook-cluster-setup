#!/usr/bin/env bash
set -euo pipefail

run_dir=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-dir)
      run_dir="$2"
      shift 2
      ;;
    --help)
      echo "Usage: bash scripts/make_submission_package.sh [--run-dir results/final_YYYYMMDD-HHMMSS]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

timestamp="$(date +%Y%m%d-%H%M%S)"
out_root="submission"
pkg="$out_root/attention_project_submission_$timestamp"
mkdir -p "$pkg"

copy_path() {
  local src="$1"
  if [[ -e "$src" ]]; then
    mkdir -p "$pkg/$(dirname "$src")"
    if [[ -d "$src" ]]; then
      tar \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        -cf - \
        -C "$(dirname "$src")" \
        "$(basename "$src")" | tar -xf - -C "$pkg/$(dirname "$src")"
    else
      cp "$src" "$pkg/$src"
    fi
  fi
}

for path in \
  README.md \
  .gitignore \
  configs/attention_experiment.env.example \
  configs/cluster.env.example \
  configs/hosts.template \
  configs/hosts \
  docs \
  report \
  src \
  scripts \
  plots \
  python_tests \
  mpi_samples \
  multipass; do
  copy_path "$path"
done

if [[ -n "$run_dir" ]]; then
  if [[ ! -d "$run_dir" ]]; then
    echo "ERROR: run dir does not exist: $run_dir"
    exit 1
  fi
  mkdir -p "$pkg/results"
  cp -R "$run_dir" "$pkg/results/"
fi

{
  echo "SUBMISSION_MANIFEST"
  date -u +"utc_time=%Y-%m-%dT%H:%M:%SZ"
  echo "git_commit=$(git rev-parse HEAD 2>/dev/null || true)"
  echo "git_status:"
  git status -sb 2>/dev/null || true
  echo
  echo "package_contents:"
  find "$pkg" -maxdepth 4 -type f | sort
} > "$pkg/SUBMISSION_MANIFEST.txt"

archive="$pkg.tar.gz"
tar -czf "$archive" -C "$out_root" "$(basename "$pkg")"

echo "SUBMISSION_DIR=$pkg"
echo "SUBMISSION_ARCHIVE=$archive"
