#include "attention_omp.hpp"

#include "attention_online.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif

static int total_rows(const Tensor4D& Q) {
    return Q.B * Q.H * Q.L;
}

static void decode_row(const Tensor4D& Q, int global_row, int& b, int& h, int& i) {
    i = global_row % Q.L;
    int bh = global_row / Q.L;
    h = bh % Q.H;
    b = bh / Q.H;
}

static double dot_qk_omp(const Tensor4D& Q, const Tensor4D& K,
                         int b, int h, int i, int j) {
    double s = 0.0;
    for (int d = 0; d < Q.Dh; d++) {
        s += (double)Q(b, h, i, d) * (double)K(b, h, j, d);
    }
    return s / std::sqrt((double)Q.Dh);
}

static void row_kernel(const Tensor4D& Q, const Tensor4D& K, const Tensor4D& V,
                       Tensor4D& O, int b, int h, int i, bool causal,
                       std::vector<double>& scores) {
    int L = Q.L;
    int Dh = Q.Dh;
    double m = -std::numeric_limits<double>::infinity();
    for (int j = 0; j < L; j++) {
        if (causal && j > i) {
            scores[j] = -std::numeric_limits<double>::infinity();
        } else {
            scores[j] = dot_qk_omp(Q, K, b, h, i, j);
            m = std::max(m, scores[j]);
        }
    }

    double denom = 0.0;
    for (int j = 0; j < L; j++) {
        if (std::isfinite(scores[j])) {
            scores[j] = std::exp(scores[j] - m);
            denom += scores[j];
        } else {
            scores[j] = 0.0;
        }
    }

    for (int d = 0; d < Dh; d++) {
        double out = 0.0;
        for (int j = 0; j < L; j++) {
            out += (scores[j] / denom) * V(b, h, j, d);
        }
        O(b, h, i, d) = (float)out;
    }
}

static int thread_id() {
#ifdef _OPENMP
    return omp_get_thread_num();
#else
    return 0;
#endif
}

static int thread_count(const Config& cfg) {
#ifdef _OPENMP
    return std::max(1, cfg.omp_threads);
#else
    return 1;
#endif
}

void attn_omp_row(const Tensor4D& Q,
                  const Tensor4D& K,
                  const Tensor4D& V,
                  Tensor4D& O,
                  const Config& cfg,
                  std::vector<ThreadStat>& thread_stats) {
    int nrows = total_rows(Q);
    int nt = thread_count(cfg);
    thread_stats.assign(nt, ThreadStat{});
    for (int t = 0; t < nt; t++) {
        thread_stats[t].thread_id = t;
    }

#pragma omp parallel
    {
        int tid = thread_id();
        std::vector<double> scores(Q.L, 0.0);
        double t0 = now_ms();
        int rows = 0;

#pragma omp for schedule(runtime)
        for (int g = 0; g < nrows; g++) {
            int b, h, i;
            decode_row(Q, g, b, h, i);
            row_kernel(Q, K, V, O, b, h, i, cfg.causal, scores);
            rows++;
        }

        double t1 = now_ms();
        if (tid < (int)thread_stats.size()) {
            thread_stats[tid].rows_done += rows;
            thread_stats[tid].thread_compute_ms += t1 - t0;
        }
    }
}

void attn_omp_online(const Tensor4D& Q,
                     const Tensor4D& K,
                     const Tensor4D& V,
                     Tensor4D& O,
                     const Config& cfg,
                     std::vector<ThreadStat>& thread_stats) {
    int nrows = total_rows(Q);
    int nt = thread_count(cfg);
    thread_stats.assign(nt, ThreadStat{});
    for (int t = 0; t < nt; t++) {
        thread_stats[t].thread_id = t;
    }

#pragma omp parallel
    {
        int tid = thread_id();
        double t0 = now_ms();
        int rows = 0;

#pragma omp for schedule(runtime)
        for (int g = 0; g < nrows; g++) {
            int b, h, i;
            decode_row(Q, g, b, h, i);
            attn_online_row(Q, K, V, O, b, h, i, cfg.Bc, cfg.causal);
            rows++;
        }

        double t1 = now_ms();
        if (tid < (int)thread_stats.size()) {
            thread_stats[tid].rows_done += rows;
            thread_stats[tid].thread_compute_ms += t1 - t0;
        }
    }
}
