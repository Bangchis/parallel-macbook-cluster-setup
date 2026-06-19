#pragma once

#include "config.hpp"
#include "metrics.hpp"

#include <string>
#include <vector>

void write_summary(const std::string& path, const Config& cfg, const Metrics& m);
void write_rank_stats(const std::string& path, const std::vector<RankStat>& ranks);
void write_thread_stats(const std::string& path, const std::vector<ThreadStat>& threads);
