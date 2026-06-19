#pragma once

#include <string>

struct Config {
    std::string algo = "serial_row";
    int B = 1;
    int H = 1;
    int L = 16;
    int Dh = 8;
    int Br = 16;
    int Bc = 64;
    bool causal = false;
    std::string assignment = "block_cyclic";
    std::string schedule = "static";
    int omp_threads = 1;
    int repeat = 1;
    bool verify = true;
    bool debug = false;
    unsigned seed = 123;
    std::string output = "results/raw/summary.csv";
    std::string run_id = "manual";
};

Config parse_args(int argc, char** argv);
void print_config(const Config& cfg);
void setup_omp(const Config& cfg);
