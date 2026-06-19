#include "attention_serial.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <vector>

static void check_attention_shape(const Tensor4D& Q, const Tensor4D& K,
                                  const Tensor4D& V, const Tensor4D& O) {
    if (Q.B != K.B || Q.B != V.B || Q.B != O.B ||
        Q.H != K.H || Q.H != V.H || Q.H != O.H ||
        Q.L != K.L || Q.L != V.L || Q.L != O.L ||
        Q.Dh != K.Dh || Q.Dh != V.Dh || Q.Dh != O.Dh) {
        throw std::runtime_error("Attention tensor shape mismatch");
    }
}

static double dot_qk(const Tensor4D& Q, const Tensor4D& K,
                     int b, int h, int i, int j) {
    double s = 0.0;
    for (int d = 0; d < Q.Dh; d++) {
        s += (double)Q(b, h, i, d) * (double)K(b, h, j, d);
    }
    return s / std::sqrt((double)Q.Dh);
}

void attn_full(const Tensor4D& Q, const Tensor4D& K,
               const Tensor4D& V, Tensor4D& O, bool causal) {
    check_attention_shape(Q, K, V, O);
    int L = Q.L;
    int Dh = Q.Dh;
    std::vector<double> S((size_t)L * L, 0.0);
    std::vector<double> P((size_t)L * L, 0.0);

    for (int b = 0; b < Q.B; b++) {
        for (int h = 0; h < Q.H; h++) {
            std::fill(S.begin(), S.end(), -std::numeric_limits<double>::infinity());
            std::fill(P.begin(), P.end(), 0.0);

            for (int i = 0; i < L; i++) {
                for (int j = 0; j < L; j++) {
                    if (!causal || j <= i) {
                        S[(size_t)i * L + j] = dot_qk(Q, K, b, h, i, j);
                    }
                }
            }

            for (int i = 0; i < L; i++) {
                double m = -std::numeric_limits<double>::infinity();
                for (int j = 0; j < L; j++) {
                    m = std::max(m, S[(size_t)i * L + j]);
                }
                double denom = 0.0;
                for (int j = 0; j < L; j++) {
                    if (std::isfinite(S[(size_t)i * L + j])) {
                        double e = std::exp(S[(size_t)i * L + j] - m);
                        P[(size_t)i * L + j] = e;
                        denom += e;
                    }
                }
                for (int j = 0; j < L; j++) {
                    P[(size_t)i * L + j] /= denom;
                }
            }

            for (int i = 0; i < L; i++) {
                for (int d = 0; d < Dh; d++) {
                    double out = 0.0;
                    for (int j = 0; j < L; j++) {
                        out += P[(size_t)i * L + j] * V(b, h, j, d);
                    }
                    O(b, h, i, d) = (float)out;
                }
            }
        }
    }
}

void attn_row(const Tensor4D& Q, const Tensor4D& K,
              const Tensor4D& V, Tensor4D& O, bool causal) {
    check_attention_shape(Q, K, V, O);
    int L = Q.L;
    int Dh = Q.Dh;
    std::vector<double> scores(L);

    for (int b = 0; b < Q.B; b++) {
        for (int h = 0; h < Q.H; h++) {
            for (int i = 0; i < L; i++) {
                double m = -std::numeric_limits<double>::infinity();
                for (int j = 0; j < L; j++) {
                    if (causal && j > i) {
                        scores[j] = -std::numeric_limits<double>::infinity();
                    } else {
                        scores[j] = dot_qk(Q, K, b, h, i, j);
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
        }
    }
}
