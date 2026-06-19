#include "tensor.hpp"

#include <random>
#include <sstream>

Tensor4D::Tensor4D() : B(0), H(0), L(0), Dh(0) {}

Tensor4D::Tensor4D(int B_, int H_, int L_, int Dh_)
    : B(B_), H(H_), L(L_), Dh(Dh_),
      data((size_t)B_ * H_ * L_ * Dh_, 0.0f) {}

size_t Tensor4D::idx(int b, int h, int i, int d) const {
    return (((size_t)b * H + h) * L + i) * Dh + d;
}

float& Tensor4D::operator()(int b, int h, int i, int d) {
    return data[idx(b, h, i, d)];
}

const float& Tensor4D::operator()(int b, int h, int i, int d) const {
    return data[idx(b, h, i, d)];
}

size_t Tensor4D::size() const {
    return data.size();
}

void Tensor4D::fill_zero() {
    std::fill(data.begin(), data.end(), 0.0f);
}

void Tensor4D::fill_random(unsigned seed) {
    std::mt19937 gen(seed);
    std::uniform_real_distribution<float> dist(-0.1f, 0.1f);
    for (float& x : data) {
        x = dist(gen);
    }
}

std::string Tensor4D::shape() const {
    std::ostringstream oss;
    oss << B << "x" << H << "x" << L << "x" << Dh;
    return oss.str();
}
