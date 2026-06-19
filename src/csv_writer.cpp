#include "csv_writer.hpp"

#include <filesystem>
#include <fstream>

static void ensure_parent(const std::string& path) {
    std::filesystem::path p(path);
    if (p.has_parent_path()) {
        std::filesystem::create_directories(p.parent_path());
    }
}

static bool empty_file(const std::string& path) {
    return !std::filesystem::exists(path) || std::filesystem::file_size(path) == 0;
}

void write_summary(const std::string& path, const Config& cfg, const Metrics& m) {
    ensure_parent(path);
    bool header = empty_file(path);
    std::ofstream out(path, std::ios::app);
    if (header) {
        out << "run_id,algorithm,B,H,L,Dh,N,Br,Bc,causal,assignment,schedule,"
            << "world_size,omp_threads,repeat,total_ms_with_comm,"
            << "total_ms_without_comm,compute_ms_max,compute_ms_avg,comm_ms_total,"
            << "bcast_ms,gather_ms,reduce_ms,checksum,max_abs_error,"
            << "mean_abs_error,relative_l2_error,speedup_with_comm,"
            << "speedup_without_comm,efficiency_with_comm,efficiency_without_comm,"
            << "memory_estimated_mb,load_imbalance\n";
    }
    out << cfg.run_id << "," << cfg.algo << "," << cfg.B << "," << cfg.H << ","
        << cfg.L << "," << cfg.Dh << "," << cfg.L << "," << cfg.Br << ","
        << cfg.Bc << "," << cfg.causal << "," << cfg.assignment << ","
        << cfg.schedule << "," << m.world_size << "," << cfg.omp_threads << ","
        << cfg.repeat << "," << m.total_ms_with_comm << ","
        << m.total_ms_without_comm << "," << m.compute_ms_max << ","
        << m.compute_ms_avg << "," << m.comm_ms_total << "," << m.bcast_ms
        << "," << m.gather_ms << "," << m.reduce_ms << "," << m.checksum
        << "," << m.max_abs_error << "," << m.mean_abs_error << ","
        << m.relative_l2_error << "," << m.speedup_with_comm << ","
        << m.speedup_without_comm << "," << m.efficiency_with_comm << ","
        << m.efficiency_without_comm << "," << m.memory_estimated_mb << ","
        << m.load_imbalance << "\n";
}

void write_rank_stats(const std::string& path, const std::vector<RankStat>& ranks) {
    ensure_parent(path);
    bool header = empty_file(path);
    std::ofstream out(path, std::ios::app);
    if (header) {
        out << "run_id,rank,hostname,rows_assigned,compute_ms,bcast_ms,gather_ms,"
            << "reduce_ms,total_ms,idle_ms,checksum_local\n";
    }
    for (const RankStat& r : ranks) {
        out << r.run_id << "," << r.rank << "," << r.hostname << ","
            << r.rows_assigned << "," << r.compute_ms << "," << r.bcast_ms
            << "," << r.gather_ms << "," << r.reduce_ms << "," << r.total_ms
            << "," << r.idle_ms << "," << r.checksum_local << "\n";
    }
}

void write_thread_stats(const std::string& path, const std::vector<ThreadStat>& threads) {
    ensure_parent(path);
    bool header = empty_file(path);
    std::ofstream out(path, std::ios::app);
    if (header) {
        out << "run_id,rank,thread_id,rows_done,thread_compute_ms\n";
    }
    for (const ThreadStat& t : threads) {
        out << t.run_id << "," << t.rank << "," << t.thread_id << ","
            << t.rows_done << "," << t.thread_compute_ms << "\n";
    }
}
