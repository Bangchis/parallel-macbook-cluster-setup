#pragma once

#include <string>
#include <vector>

struct ThreadStat {
    std::string run_id = "manual";
    int rank = 0;
    int thread_id = 0;
    int rows_done = 0;
    double thread_compute_ms = 0.0;
};

struct RankStat {
    std::string run_id = "manual";
    int rank = 0;
    std::string hostname = "unknown";
    int rows_assigned = 0;
    double compute_ms = 0.0;
    double bcast_ms = 0.0;
    double gather_ms = 0.0;
    double reduce_ms = 0.0;
    double total_ms = 0.0;
    double idle_ms = 0.0;
    double checksum_local = 0.0;
};

struct Metrics {
    std::string run_id = "manual";
    int world_size = 1;
    double total_ms_with_comm = 0.0;
    double total_ms_without_comm = 0.0;
    double compute_ms_max = 0.0;
    double compute_ms_avg = 0.0;
    double comm_ms_total = 0.0;
    double bcast_ms = 0.0;
    double gather_ms = 0.0;
    double reduce_ms = 0.0;
    double checksum = 0.0;
    double max_abs_error = 0.0;
    double mean_abs_error = 0.0;
    double relative_l2_error = 0.0;
    double speedup_with_comm = 0.0;
    double speedup_without_comm = 0.0;
    double efficiency_with_comm = 0.0;
    double efficiency_without_comm = 0.0;
    double memory_estimated_mb = 0.0;
    double load_imbalance = 1.0;
};

double now_ms();
double calc_load_balance(const std::vector<RankStat>& ranks);
double calc_speedup(double t1, double tp);
double calc_efficiency(double speedup, int p);
std::string get_hostname();
