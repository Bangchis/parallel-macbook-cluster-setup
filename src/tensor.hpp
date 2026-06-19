#pragma once

#include <cstddef>
#include <string>
#include <vector>

struct Tensor4D {
    int B, H, L, Dh;
    std::vector<float> data;

    Tensor4D();
    Tensor4D(int B_, int H_, int L_, int Dh_);

    size_t idx(int b, int h, int i, int d) const;
    float& operator()(int b, int h, int i, int d);
    const float& operator()(int b, int h, int i, int d) const;

    size_t size() const;
    void fill_zero();
    void fill_random(unsigned seed);
    std::string shape() const;
};
