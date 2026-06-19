#include "attention_online.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <vector>

static double dot_qk_online(const Tensor4D& Q, const Tensor4D& K,
                            int b, int h, int i, int j) {
    double s = 0.0;
    for (int d = 0; d < Q.Dh; d++) {
        s += (double)Q(b, h, i, d) * (double)K(b, h, j, d);
    }
    return s / std::sqrt((double)Q.Dh);
}

void attn_online_row(const Tensor4D& Q,
                     const Tensor4D& K,
                     const Tensor4D& V,
                     Tensor4D& O,
                     int b, int h, int i,
                     int Bc,
                     bool causal) {
    int L = Q.L;
    int Dh = Q.Dh;
    double m = -std::numeric_limits<double>::infinity();
    double l = 0.0;
    std::vector<double> out(Dh, 0.0);
    std::vector<double> scores(Bc, 0.0);

    for (int kb = 0; kb < L; kb += Bc) {
        int end = std::min(kb + Bc, L);
        if (causal && kb > i) {
            break;
        }

        double m_block = -std::numeric_limits<double>::infinity();
        for (int j = kb; j < end; j++) {
            int t = j - kb;
            if (causal && j > i) {
                scores[t] = -std::numeric_limits<double>::infinity();
            } else {
                scores[t] = dot_qk_online(Q, K, b, h, i, j);
                m_block = std::max(m_block, scores[t]);
            }
        }
        if (!std::isfinite(m_block)) {
            continue;
        }

        double m_new = std::max(m, m_block);
        double alpha = std::isfinite(m) ? std::exp(m - m_new) : 0.0;
        for (int d = 0; d < Dh; d++) {
            out[d] *= alpha;
        }
        l *= alpha;

        for (int j = kb; j < end; j++) {
            int t = j - kb;
            if (!std::isfinite(scores[t])) {
                continue;
            }
            double w = std::exp(scores[t] - m_new);
            l += w;
            for (int d = 0; d < Dh; d++) {
                out[d] += w * V(b, h, j, d);
            }
        }
        m = m_new;
    }

    for (int d = 0; d < Dh; d++) {
        O(b, h, i, d) = (float)(out[d] / l);
    }
}
