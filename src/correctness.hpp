#pragma once

#include "tensor.hpp"

struct ErrorStat {
    double max_abs_error = 0.0;
    double mean_abs_error = 0.0;
    double relative_l2_error = 0.0;
};

ErrorStat check_error(const Tensor4D& A, const Tensor4D& B);
double checksum(const Tensor4D& T);
bool error_ok(const ErrorStat& e, double tol);
