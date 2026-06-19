#include "metrics.hpp"

#include <algorithm>
#include <chrono>
#include <numeric>
#include <unistd.h>

double now_ms() {
    using clock = std::chrono::steady_clock;
    auto t = clock::now().time_since_epoch();
    return std::chrono::duration<double, std::milli>(t).count();
}

double calc_load_balance(const std::vector<RankStat>& ranks) {
    if (ranks.empty()) return 1.0;
    double sum = 0.0;
    double mx = 0.0;
    for (const RankStat& r : ranks) {
        sum += r.compute_ms;
        mx = std::max(mx, r.compute_ms);
    }
    double avg = sum / (double)ranks.size();
    return avg > 0.0 ? mx / avg : 1.0;
}

double calc_speedup(double t1, double tp) {
    return tp > 0.0 ? t1 / tp : 0.0;
}

double calc_efficiency(double speedup, int p) {
    return p > 0 ? speedup / (double)p : 0.0;
}

std::string get_hostname() {
    char name[256];
    if (gethostname(name, sizeof(name)) != 0) {
        return "unknown";
    }
    name[sizeof(name) - 1] = '\0';
    return std::string(name);
}
