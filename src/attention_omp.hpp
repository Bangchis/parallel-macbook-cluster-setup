#pragma once

#include "config.hpp"
#include "metrics.hpp"
#include "tensor.hpp"

#include <vector>

void attn_omp_row(const Tensor4D& Q,
                  const Tensor4D& K,
                  const Tensor4D& V,
                  Tensor4D& O,
                  const Config& cfg,
                  std::vector<ThreadStat>& thread_stats);

void attn_omp_online(const Tensor4D& Q,
                     const Tensor4D& K,
                     const Tensor4D& V,
                     Tensor4D& O,
                     const Config& cfg,
                     std::vector<ThreadStat>& thread_stats);
