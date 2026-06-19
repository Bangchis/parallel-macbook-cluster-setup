#!/usr/bin/env bash
set -euo pipefail

mkdir -p build
if [[ "$(uname -s)" == "Darwin" ]]; then
  if ! command -v g++-15 >/dev/null 2>&1; then
    echo "Missing g++-15. Install GCC with: brew install gcc" >&2
    exit 1
  fi
  OMPI_CXX=g++-15 mpicxx -O3 -std=c++17 -fopenmp src/*.cpp -o build/attention_bench
else
  mpicxx -O3 -std=c++17 -fopenmp src/*.cpp -o build/attention_bench
fi
echo "BUILD_OK"
