#include "config.hpp"

#include <array>
#include <iostream>
#include <stdexcept>
#include <string>

#ifdef _OPENMP
#include <omp.h>
#endif

static bool to_bool(const std::string& s) {
    return s == "1" || s == "true" || s == "yes";
}

template <size_t N>
static bool one_of(const std::string& value, const std::array<const char*, N>& valid) {
    for (const char* item : valid) {
        if (value == item) {
            return true;
        }
    }
    return false;
}

template <size_t N>
static std::string join_values(const std::array<const char*, N>& valid) {
    std::string out;
    for (size_t i = 0; i < valid.size(); i++) {
        if (i > 0) {
            out += ", ";
        }
        out += valid[i];
    }
    return out;
}

static std::string need_value(int& i, int argc, char** argv) {
    if (i + 1 >= argc) {
        throw std::runtime_error(std::string("Missing value for ") + argv[i]);
    }
    return argv[++i];
}

Config parse_args(int argc, char** argv) {
    static constexpr std::array<const char*, 8> algos = {
        "serial_full", "serial_row", "omp_row", "omp_online",
        "mpi_row", "mpi_online", "mpi_row_nb", "mpi_online_nb",
    };
    static constexpr std::array<const char*, 3> assignments = {
        "contiguous", "cyclic", "block_cyclic",
    };
    static constexpr std::array<const char*, 3> schedules = {
        "static", "dynamic", "guided",
    };

    Config cfg;
    for (int i = 1; i < argc; i++) {
        std::string a = argv[i];
        if (a == "--algo") cfg.algo = need_value(i, argc, argv);
        else if (a == "--B") cfg.B = std::stoi(need_value(i, argc, argv));
        else if (a == "--H") cfg.H = std::stoi(need_value(i, argc, argv));
        else if (a == "--L") cfg.L = std::stoi(need_value(i, argc, argv));
        else if (a == "--Dh") cfg.Dh = std::stoi(need_value(i, argc, argv));
        else if (a == "--Br") cfg.Br = std::stoi(need_value(i, argc, argv));
        else if (a == "--Bc") cfg.Bc = std::stoi(need_value(i, argc, argv));
        else if (a == "--causal") cfg.causal = to_bool(need_value(i, argc, argv));
        else if (a == "--assignment") cfg.assignment = need_value(i, argc, argv);
        else if (a == "--schedule") cfg.schedule = need_value(i, argc, argv);
        else if (a == "--omp_threads") cfg.omp_threads = std::stoi(need_value(i, argc, argv));
        else if (a == "--repeat") cfg.repeat = std::stoi(need_value(i, argc, argv));
        else if (a == "--verify") cfg.verify = to_bool(need_value(i, argc, argv));
        else if (a == "--debug") cfg.debug = to_bool(need_value(i, argc, argv));
        else if (a == "--seed") cfg.seed = (unsigned)std::stoul(need_value(i, argc, argv));
        else if (a == "--output") cfg.output = need_value(i, argc, argv);
        else if (a == "--run_id") cfg.run_id = need_value(i, argc, argv);
        else if (a == "--help") {
            std::cout << "Options: --algo --B --H --L --Dh --Br --Bc --causal "
                      << "--assignment --schedule --omp_threads --repeat "
                      << "--verify --debug --seed --output --run_id\n";
            std::cout << "Algorithms: " << join_values(algos) << "\n";
            std::cout << "Assignments: " << join_values(assignments) << "\n";
            std::cout << "OpenMP schedules: " << join_values(schedules) << "\n";
            std::exit(0);
        } else {
            throw std::runtime_error("Unknown option: " + a);
        }
    }

    if (cfg.B <= 0 || cfg.H <= 0 || cfg.L <= 0 || cfg.Dh <= 0) {
        throw std::runtime_error("B, H, L, Dh must be positive");
    }
    if (cfg.Br <= 0 || cfg.Bc <= 0 || cfg.omp_threads <= 0 || cfg.repeat <= 0) {
        throw std::runtime_error("Br, Bc, omp_threads, repeat must be positive");
    }
    if (!one_of(cfg.algo, algos)) {
        throw std::runtime_error("Unknown algorithm '" + cfg.algo +
                                 "'. Valid algorithms: " + join_values(algos));
    }
    if (!one_of(cfg.assignment, assignments)) {
        throw std::runtime_error("Unknown assignment '" + cfg.assignment +
                                 "'. Valid assignments: " + join_values(assignments));
    }
    if (!one_of(cfg.schedule, schedules)) {
        throw std::runtime_error("Unknown schedule '" + cfg.schedule +
                                 "'. Valid schedules: " + join_values(schedules));
    }
    return cfg;
}

void print_config(const Config& cfg) {
    std::cout << "CONFIG algo=" << cfg.algo
              << " B=" << cfg.B << " H=" << cfg.H
              << " L=" << cfg.L << " Dh=" << cfg.Dh
              << " Br=" << cfg.Br << " Bc=" << cfg.Bc
              << " causal=" << cfg.causal
              << " assignment=" << cfg.assignment
              << " schedule=" << cfg.schedule
              << " omp_threads=" << cfg.omp_threads
              << " repeat=" << cfg.repeat
              << " verify=" << cfg.verify
              << " output=" << cfg.output << "\n";
}

void setup_omp(const Config& cfg) {
#ifdef _OPENMP
    omp_set_num_threads(cfg.omp_threads);
    omp_sched_t sched = omp_sched_static;
    if (cfg.schedule == "dynamic") sched = omp_sched_dynamic;
    if (cfg.schedule == "guided") sched = omp_sched_guided;
    omp_set_schedule(sched, 1);
#else
    (void)cfg;
#endif
}
