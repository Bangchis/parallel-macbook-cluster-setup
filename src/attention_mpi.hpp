#pragma once

#include "config.hpp"
#include "metrics.hpp"
#include "tensor.hpp"

#include <vector>

bool row_belongs_to_rank(int global_row, int total_rows, const Config& cfg,
                         int rank, int world_size);

void attn_mpi_online(const Tensor4D& Q_root,
                     const Tensor4D& K_root,
                     const Tensor4D& V_root,
                     Tensor4D& O_root,
                     const Config& cfg,
                     int rank,
                     int world_size,
                     Metrics& metrics,
                     std::vector<RankStat>& rank_stats,
                     std::vector<ThreadStat>& thread_stats);

void attn_mpi_row(const Tensor4D& Q_root,
                  const Tensor4D& K_root,
                  const Tensor4D& V_root,
                  Tensor4D& O_root,
                  const Config& cfg,
                  int rank,
                  int world_size,
                  Metrics& metrics,
                  std::vector<RankStat>& rank_stats,
                  std::vector<ThreadStat>& thread_stats);

void attn_mpi_online_nb(const Tensor4D& Q_root,
                        const Tensor4D& K_root,
                        const Tensor4D& V_root,
                        Tensor4D& O_root,
                        const Config& cfg,
                        int rank,
                        int world_size,
                        Metrics& metrics,
                        std::vector<RankStat>& rank_stats,
                        std::vector<ThreadStat>& thread_stats);

void attn_mpi_row_nb(const Tensor4D& Q_root,
                     const Tensor4D& K_root,
                     const Tensor4D& V_root,
                     Tensor4D& O_root,
                     const Config& cfg,
                     int rank,
                     int world_size,
                     Metrics& metrics,
                     std::vector<RankStat>& rank_stats,
                     std::vector<ThreadStat>& thread_stats);
