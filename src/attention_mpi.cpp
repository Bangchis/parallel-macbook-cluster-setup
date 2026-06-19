#include "attention_mpi.hpp"

#include "attention_online.hpp"
#include "correctness.hpp"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <limits>
#include <mpi.h>
#include <numeric>

#ifdef _OPENMP
#include <omp.h>
#endif

static int total_rows(const Config& cfg) {
    return cfg.B * cfg.H * cfg.L;
}

static void decode_row(const Config& cfg, int global_row, int& b, int& h, int& i) {
    i = global_row % cfg.L;
    int bh = global_row / cfg.L;
    h = bh % cfg.H;
    b = bh / cfg.H;
}

bool row_belongs_to_rank(int global_row, int total_rows_, const Config& cfg,
                         int rank, int world_size) {
    if (cfg.assignment == "cyclic") {
        return global_row % world_size == rank;
    }
    if (cfg.assignment == "contiguous") {
        int base = total_rows_ / world_size;
        int rem = total_rows_ % world_size;
        int start = rank * base + std::min(rank, rem);
        int count = base + (rank < rem ? 1 : 0);
        return global_row >= start && global_row < start + count;
    }
    int block_id = global_row / cfg.Br;
    return block_id % world_size == rank;
}

static void bcast_tensor(Tensor4D& T, int root) {
    MPI_Bcast(T.data.data(), (int)T.data.size(), MPI_FLOAT, root, MPI_COMM_WORLD);
}

static double dot_qk_mpi(const Tensor4D& Q, const Tensor4D& K,
                         int b, int h, int i, int j) {
    double s = 0.0;
    for (int d = 0; d < Q.Dh; d++) {
        s += (double)Q(b, h, i, d) * (double)K(b, h, j, d);
    }
    return s / std::sqrt((double)Q.Dh);
}

static void attn_row_one_mpi(const Tensor4D& Q, const Tensor4D& K, const Tensor4D& V,
                             Tensor4D& O, int b, int h, int i, bool causal,
                             std::vector<double>& scores) {
    double m = -std::numeric_limits<double>::infinity();
    for (int j = 0; j < Q.L; j++) {
        if (causal && j > i) {
            scores[j] = -std::numeric_limits<double>::infinity();
        } else {
            scores[j] = dot_qk_mpi(Q, K, b, h, i, j);
            m = std::max(m, scores[j]);
        }
    }
    double denom = 0.0;
    for (int j = 0; j < Q.L; j++) {
        if (std::isfinite(scores[j])) {
            scores[j] = std::exp(scores[j] - m);
            denom += scores[j];
        } else {
            scores[j] = 0.0;
        }
    }
    for (int d = 0; d < Q.Dh; d++) {
        double out = 0.0;
        for (int j = 0; j < Q.L; j++) {
            out += (scores[j] / denom) * V(b, h, j, d);
        }
        O(b, h, i, d) = (float)out;
    }
}

static void attn_mpi_impl(const Tensor4D& Q_root,
                          const Tensor4D& K_root,
                          const Tensor4D& V_root,
                          Tensor4D& O_root,
                          const Config& cfg,
                          int rank,
                          int world_size,
                          Metrics& metrics,
                          std::vector<RankStat>& rank_stats,
                          std::vector<ThreadStat>& thread_stats,
                          bool online) {
    Tensor4D Q(cfg.B, cfg.H, cfg.L, cfg.Dh);
    Tensor4D K(cfg.B, cfg.H, cfg.L, cfg.Dh);
    Tensor4D V(cfg.B, cfg.H, cfg.L, cfg.Dh);
    if (rank == 0) {
        Q = Q_root;
        K = K_root;
        V = V_root;
    }

    MPI_Barrier(MPI_COMM_WORLD);
    double total0 = now_ms();
    double b0 = now_ms();
    bcast_tensor(Q, 0);
    bcast_tensor(K, 0);
    bcast_tensor(V, 0);
    double b1 = now_ms();

    Tensor4D local_O(cfg.B, cfg.H, cfg.L, cfg.Dh);
    local_O.fill_zero();

    int nrows = total_rows(cfg);
    int rows_assigned = 0;
    int nt = std::max(1, cfg.omp_threads);
    thread_stats.assign(nt, ThreadStat{});
    for (int t = 0; t < nt; t++) {
        thread_stats[t].rank = rank;
        thread_stats[t].thread_id = t;
    }

    MPI_Barrier(MPI_COMM_WORLD);
    double c0 = now_ms();
#pragma omp parallel
    {
#ifdef _OPENMP
        int tid = omp_get_thread_num();
#else
        int tid = 0;
#endif
        int local_rows = 0;
        double t0 = now_ms();
        std::vector<double> scores(cfg.L, 0.0);

#pragma omp for schedule(runtime)
        for (int g = 0; g < nrows; g++) {
            if (!row_belongs_to_rank(g, nrows, cfg, rank, world_size)) {
                continue;
            }
            int b, h, i;
            decode_row(cfg, g, b, h, i);
            if (online) {
                attn_online_row(Q, K, V, local_O, b, h, i, cfg.Bc, cfg.causal);
            } else {
                attn_row_one_mpi(Q, K, V, local_O, b, h, i, cfg.causal, scores);
            }
            local_rows++;
        }

        double t1 = now_ms();
        if (tid < (int)thread_stats.size()) {
            thread_stats[tid].rows_done += local_rows;
            thread_stats[tid].thread_compute_ms += t1 - t0;
        }
#pragma omp atomic
        rows_assigned += local_rows;
    }
    double c1 = now_ms();

    O_root = Tensor4D(cfg.B, cfg.H, cfg.L, cfg.Dh);
    double g0 = now_ms();
    MPI_Reduce(local_O.data.data(), O_root.data.data(), (int)local_O.data.size(),
               MPI_FLOAT, MPI_SUM, 0, MPI_COMM_WORLD);
    double g1 = now_ms();

    double local_checksum = checksum(local_O);
    double global_checksum = 0.0;
    double r0 = now_ms();
    MPI_Reduce(&local_checksum, &global_checksum, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
    double r1 = now_ms();

    double compute_ms = c1 - c0;
    double bcast_ms = b1 - b0;
    double gather_ms = g1 - g0;
    double reduce_ms = r1 - r0;
    double total_ms = now_ms() - total0;

    std::vector<double> all_compute(world_size);
    std::vector<double> all_bcast(world_size);
    std::vector<double> all_gather(world_size);
    std::vector<double> all_reduce(world_size);
    std::vector<double> all_total(world_size);
    std::vector<double> all_checksum(world_size);
    std::vector<int> all_rows(world_size);
    char local_host[128];
    std::memset(local_host, 0, sizeof(local_host));
    std::string host = get_hostname();
    std::strncpy(local_host, host.c_str(), sizeof(local_host) - 1);
    std::vector<char> all_hosts((size_t)world_size * sizeof(local_host));
    MPI_Gather(&compute_ms, 1, MPI_DOUBLE, all_compute.data(), 1, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Gather(&bcast_ms, 1, MPI_DOUBLE, all_bcast.data(), 1, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Gather(&gather_ms, 1, MPI_DOUBLE, all_gather.data(), 1, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Gather(&reduce_ms, 1, MPI_DOUBLE, all_reduce.data(), 1, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Gather(&total_ms, 1, MPI_DOUBLE, all_total.data(), 1, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Gather(&local_checksum, 1, MPI_DOUBLE, all_checksum.data(), 1, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Gather(&rows_assigned, 1, MPI_INT, all_rows.data(), 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Gather(local_host, (int)sizeof(local_host), MPI_CHAR,
               all_hosts.data(), (int)sizeof(local_host), MPI_CHAR, 0, MPI_COMM_WORLD);

    std::vector<int> local_thread_rows(nt, 0);
    std::vector<double> local_thread_ms(nt, 0.0);
    for (int t = 0; t < nt && t < (int)thread_stats.size(); t++) {
        local_thread_rows[t] = thread_stats[t].rows_done;
        local_thread_ms[t] = thread_stats[t].thread_compute_ms;
    }
    std::vector<int> all_thread_rows((size_t)world_size * nt);
    std::vector<double> all_thread_ms((size_t)world_size * nt);
    MPI_Gather(local_thread_rows.data(), nt, MPI_INT,
               all_thread_rows.data(), nt, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Gather(local_thread_ms.data(), nt, MPI_DOUBLE,
               all_thread_ms.data(), nt, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        rank_stats.clear();
        metrics.world_size = world_size;
        metrics.compute_ms_max = *std::max_element(all_compute.begin(), all_compute.end());
        metrics.compute_ms_avg = std::accumulate(all_compute.begin(), all_compute.end(), 0.0) / world_size;
        metrics.bcast_ms = *std::max_element(all_bcast.begin(), all_bcast.end());
        metrics.gather_ms = *std::max_element(all_gather.begin(), all_gather.end());
        metrics.reduce_ms = *std::max_element(all_reduce.begin(), all_reduce.end());
        metrics.comm_ms_total = metrics.bcast_ms + metrics.gather_ms + metrics.reduce_ms;
        metrics.total_ms_without_comm = metrics.compute_ms_max;
        metrics.total_ms_with_comm = *std::max_element(all_total.begin(), all_total.end());
        metrics.checksum = global_checksum;

        double max_compute = metrics.compute_ms_max;
        for (int r = 0; r < world_size; r++) {
            RankStat st;
            st.run_id = cfg.run_id;
            st.rank = r;
            st.hostname = std::string(all_hosts.data() + (size_t)r * sizeof(local_host));
            st.rows_assigned = all_rows[r];
            st.compute_ms = all_compute[r];
            st.bcast_ms = all_bcast[r];
            st.gather_ms = all_gather[r];
            st.reduce_ms = all_reduce[r];
            st.total_ms = all_total[r];
            st.idle_ms = std::max(0.0, max_compute - all_compute[r]);
            st.checksum_local = all_checksum[r];
            rank_stats.push_back(st);
        }
        metrics.load_imbalance = calc_load_balance(rank_stats);

        thread_stats.clear();
        for (int r = 0; r < world_size; r++) {
            for (int t = 0; t < nt; t++) {
                size_t k = (size_t)r * nt + t;
                ThreadStat ts;
                ts.rank = r;
                ts.thread_id = t;
                ts.rows_done = all_thread_rows[k];
                ts.thread_compute_ms = all_thread_ms[k];
                thread_stats.push_back(ts);
            }
        }
    }
}

void attn_mpi_online(const Tensor4D& Q_root,
                     const Tensor4D& K_root,
                     const Tensor4D& V_root,
                     Tensor4D& O_root,
                     const Config& cfg,
                     int rank,
                     int world_size,
                     Metrics& metrics,
                     std::vector<RankStat>& rank_stats,
                     std::vector<ThreadStat>& thread_stats) {
    attn_mpi_impl(Q_root, K_root, V_root, O_root, cfg, rank, world_size,
                  metrics, rank_stats, thread_stats, true);
}

void attn_mpi_row(const Tensor4D& Q_root,
                  const Tensor4D& K_root,
                  const Tensor4D& V_root,
                  Tensor4D& O_root,
                  const Config& cfg,
                  int rank,
                  int world_size,
                  Metrics& metrics,
                  std::vector<RankStat>& rank_stats,
                  std::vector<ThreadStat>& thread_stats) {
    attn_mpi_impl(Q_root, K_root, V_root, O_root, cfg, rank, world_size,
                  metrics, rank_stats, thread_stats, false);
}
