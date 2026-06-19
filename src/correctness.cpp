#include "correctness.hpp"

#include <cmath>
#include <stdexcept>

static void same_shape(const Tensor4D& A, const Tensor4D& B) {
    if (A.B != B.B || A.H != B.H || A.L != B.L || A.Dh != B.Dh) {
        throw std::runtime_error("Tensor shape mismatch");
    }
}

ErrorStat check_error(const Tensor4D& A, const Tensor4D& B) {
    same_shape(A, B);
    ErrorStat e;
    double sum_abs = 0.0;
    double sum_sq = 0.0;
    double ref_sq = 0.0;

    for (size_t i = 0; i < A.data.size(); i++) {
        double diff = (double)A.data[i] - (double)B.data[i];
        double adiff = std::abs(diff);
        e.max_abs_error = std::max(e.max_abs_error, adiff);
        sum_abs += adiff;
        sum_sq += diff * diff;
        ref_sq += (double)A.data[i] * (double)A.data[i];
    }

    if (!A.data.empty()) {
        e.mean_abs_error = sum_abs / (double)A.data.size();
    }
    e.relative_l2_error = std::sqrt(sum_sq) / (std::sqrt(ref_sq) + 1e-12);
    return e;
}

double checksum(const Tensor4D& T) {
    double s = 0.0;
    for (float x : T.data) {
        s += x;
    }
    return s;
}

bool error_ok(const ErrorStat& e, double tol) {
    return e.max_abs_error <= tol && e.relative_l2_error <= tol;
}
