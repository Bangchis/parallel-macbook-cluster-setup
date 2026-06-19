#include "memory_model.hpp"

static double mb(double bytes) {
    return bytes / (1024.0 * 1024.0);
}

double mem_naive(const Config& cfg) {
    double matrices = 2.0 * cfg.B * cfg.H * cfg.L * cfg.L * sizeof(float);
    return mb(matrices);
}

double mem_rowwise(const Config& cfg) {
    double scores = (double)cfg.L * sizeof(double);
    return mb(scores);
}

double mem_online(const Config& cfg) {
    double scores = (double)cfg.Bc * sizeof(double);
    double out = (double)cfg.Dh * sizeof(double);
    return mb(scores + out);
}
