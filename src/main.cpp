#include "attention_mpi.hpp"
#include "attention_omp.hpp"
#include "attention_serial.hpp"
#include "config.hpp"
#include "correctness.hpp"
#include "csv_writer.hpp"
#include "memory_model.hpp"
#include "metrics.hpp"
#include "tensor.hpp"

#include <filesystem>
#include <cmath>
#include <fstream>
#include <iostream>
#include <mpi.h>
#include <limits>
#include <stdexcept>
#include <vector>

static void make_inputs(const Config& cfg, Tensor4D& Q, Tensor4D& K, Tensor4D& V) {
    Q = Tensor4D(cfg.B, cfg.H, cfg.L, cfg.Dh);
    K = Tensor4D(cfg.B, cfg.H, cfg.L, cfg.Dh);
    V = Tensor4D(cfg.B, cfg.H, cfg.L, cfg.Dh);
    Q.fill_random(cfg.seed + 1);
    K.fill_random(cfg.seed + 2);
    V.fill_random(cfg.seed + 3);
}

static std::string sibling_csv(const std::string& output, const std::string& name) {
    std::filesystem::path p(output);
    if (p.has_parent_path()) {
        return (p.parent_path() / name).string();
    }
    return name;
}

static double memory_for_algo(const Config& cfg) {
    if (cfg.algo == "serial_full") return mem_naive(cfg);
    if (cfg.algo == "serial_row" || cfg.algo == "omp_row" || cfg.algo == "mpi_row") {
        return mem_rowwise(cfg);
    }
    return mem_online(cfg);
}

static bool should_verify(const Config& cfg) {
    return cfg.verify && cfg.L <= 512;
}

static void print_error(const ErrorStat& e) {
    std::cout << "max_abs_error=" << e.max_abs_error
              << " mean_abs_error=" << e.mean_abs_error
              << " relative_l2_error=" << e.relative_l2_error << "\n";
}

static double dump_dot_qk(const Tensor4D& Q, const Tensor4D& K,
                          int b, int h, int i, int j) {
    double s = 0.0;
    for (int d = 0; d < Q.Dh; d++) {
        s += (double)Q(b, h, i, d) * (double)K(b, h, j, d);
    }
    return s / std::sqrt((double)Q.Dh);
}

static void write_attention_dump(const std::string& path,
                                 const Tensor4D& Q,
                                 const Tensor4D& K,
                                 const Config& cfg) {
    if (cfg.L > 64) {
        return;
    }
    std::filesystem::path p(path);
    if (p.has_parent_path()) {
        std::filesystem::create_directories(p.parent_path());
    }
    std::ofstream out(path);
    out << "i,j,p\n";
    std::vector<double> scores(cfg.L);
    int b = 0;
    int h = 0;
    for (int i = 0; i < cfg.L; i++) {
        double m = -std::numeric_limits<double>::infinity();
        for (int j = 0; j < cfg.L; j++) {
            if (cfg.causal && j > i) {
                scores[j] = -std::numeric_limits<double>::infinity();
            } else {
                scores[j] = dump_dot_qk(Q, K, b, h, i, j);
                m = std::max(m, scores[j]);
            }
        }
        double denom = 0.0;
        for (int j = 0; j < cfg.L; j++) {
            if (std::isfinite(scores[j])) {
                scores[j] = std::exp(scores[j] - m);
                denom += scores[j];
            } else {
                scores[j] = 0.0;
            }
        }
        for (int j = 0; j < cfg.L; j++) {
            out << i << "," << j << "," << (scores[j] / denom) << "\n";
        }
    }
}

static int run_root_algo(const Config& cfg, int rank, Tensor4D& Q, Tensor4D& K,
                         Tensor4D& V, Tensor4D& O, Metrics& metrics,
                         std::vector<ThreadStat>& thread_stats) {
    if (rank != 0) return 0;

    double t0 = now_ms();
    if (cfg.algo == "serial_full") {
        attn_full(Q, K, V, O, cfg.causal);
    } else if (cfg.algo == "serial_row") {
        attn_row(Q, K, V, O, cfg.causal);
    } else if (cfg.algo == "omp_row") {
        attn_omp_row(Q, K, V, O, cfg, thread_stats);
    } else if (cfg.algo == "omp_online") {
        attn_omp_online(Q, K, V, O, cfg, thread_stats);
    } else {
        return 1;
    }
    double t1 = now_ms();

    metrics.world_size = 1;
    metrics.total_ms_with_comm = t1 - t0;
    metrics.total_ms_without_comm = t1 - t0;
    metrics.compute_ms_max = t1 - t0;
    metrics.compute_ms_avg = t1 - t0;
    metrics.checksum = checksum(O);
    return 0;
}

static void add_metrics(Metrics& a, const Metrics& b) {
    a.total_ms_with_comm += b.total_ms_with_comm;
    a.total_ms_without_comm += b.total_ms_without_comm;
    a.compute_ms_max += b.compute_ms_max;
    a.compute_ms_avg += b.compute_ms_avg;
    a.comm_ms_total += b.comm_ms_total;
    a.bcast_ms += b.bcast_ms;
    a.gather_ms += b.gather_ms;
    a.reduce_ms += b.reduce_ms;
    a.load_imbalance += b.load_imbalance;
}

static void div_metrics(Metrics& a, double n) {
    a.total_ms_with_comm /= n;
    a.total_ms_without_comm /= n;
    a.compute_ms_max /= n;
    a.compute_ms_avg /= n;
    a.comm_ms_total /= n;
    a.bcast_ms /= n;
    a.gather_ms /= n;
    a.reduce_ms /= n;
    a.load_imbalance /= n;
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int rank = 0;
    int world_size = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);

    int exit_code = 0;
    try {
        Config cfg = parse_args(argc, argv);
        setup_omp(cfg);
        Metrics metrics;
        metrics.run_id = cfg.run_id;
        metrics.world_size = world_size;
        std::vector<RankStat> rank_stats;
        std::vector<ThreadStat> thread_stats;

        Tensor4D Q, K, V;
        if (rank == 0) {
            make_inputs(cfg, Q, K, V);
            if (cfg.debug) {
                print_config(cfg);
                std::cout << "tensor_shape=" << Q.shape() << "\n";
            }
        }

        Tensor4D O(cfg.B, cfg.H, cfg.L, cfg.Dh);
        Metrics sum_metrics;
        sum_metrics.run_id = cfg.run_id;
        sum_metrics.world_size = world_size;

        for (int rep = 0; rep < cfg.repeat; rep++) {
            Metrics run_metrics;
            run_metrics.run_id = cfg.run_id;
            run_metrics.world_size = world_size;
            std::vector<RankStat> run_rank_stats;
            std::vector<ThreadStat> run_thread_stats;
            Tensor4D run_O(cfg.B, cfg.H, cfg.L, cfg.Dh);

            if (cfg.algo == "mpi_online") {
                attn_mpi_online(Q, K, V, run_O, cfg, rank, world_size,
                                run_metrics, run_rank_stats, run_thread_stats);
            } else if (cfg.algo == "mpi_row") {
                attn_mpi_row(Q, K, V, run_O, cfg, rank, world_size,
                             run_metrics, run_rank_stats, run_thread_stats);
            } else {
                exit_code = run_root_algo(cfg, rank, Q, K, V, run_O,
                                          run_metrics, run_thread_stats);
            }

            if (rank == 0 && exit_code == 0) {
                add_metrics(sum_metrics, run_metrics);
                O = run_O;
                rank_stats = run_rank_stats;
                thread_stats = run_thread_stats;
            }
        }

        if (rank == 0 && exit_code == 0) {
            metrics = sum_metrics;
            div_metrics(metrics, (double)cfg.repeat);
            metrics.run_id = cfg.run_id;
            metrics.world_size = world_size;
            metrics.checksum = checksum(O);
        }

        if (rank == 0 && exit_code == 0) {
            metrics.memory_estimated_mb = memory_for_algo(cfg);
            ErrorStat err;
            bool pass = true;
            if (should_verify(cfg)) {
                Tensor4D ref(cfg.B, cfg.H, cfg.L, cfg.Dh);
                attn_row(Q, K, V, ref, cfg.causal);
                err = check_error(ref, O);
                metrics.max_abs_error = err.max_abs_error;
                metrics.mean_abs_error = err.mean_abs_error;
                metrics.relative_l2_error = err.relative_l2_error;
                pass = error_ok(err, cfg.L <= 64 ? 1e-5 : 1e-4);
            }

            std::cout << "ALGO_DONE=" << cfg.algo << "\n";
            std::cout << "checksum=" << metrics.checksum << "\n";
            print_error(err);
            std::cout << "CORRECTNESS_PASS=" << (pass ? "YES" : "NO") << "\n";
            std::cout << "total_ms_with_comm=" << metrics.total_ms_with_comm
                      << " total_ms_without_comm=" << metrics.total_ms_without_comm
                      << " compute_ms_max=" << metrics.compute_ms_max << "\n";

            if (!cfg.output.empty()) {
                write_summary(cfg.output, cfg, metrics);
                std::string common_summary = sibling_csv(cfg.output, "summary.csv");
                if (std::filesystem::path(cfg.output).filename() != "summary.csv") {
                    write_summary(common_summary, cfg, metrics);
                }
                write_rank_stats(sibling_csv(cfg.output, "rank_metrics.csv"), rank_stats);
                for (ThreadStat& t : thread_stats) {
                    t.run_id = cfg.run_id;
                }
                write_thread_stats(sibling_csv(cfg.output, "thread_metrics.csv"), thread_stats);
                if (cfg.debug && cfg.L <= 64) {
                    write_attention_dump(sibling_csv(cfg.output, "attention_dump.csv"), Q, K, cfg);
                }
            }

            if (!pass) {
                exit_code = 2;
            }
        }

        MPI_Bcast(&exit_code, 1, MPI_INT, 0, MPI_COMM_WORLD);
    } catch (const std::exception& e) {
        if (rank == 0) {
            std::cerr << "ERROR: " << e.what() << "\n";
        }
        exit_code = 1;
    }

    MPI_Finalize();
    return exit_code;
}
