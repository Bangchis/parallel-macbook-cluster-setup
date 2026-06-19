#pragma once

#include "tensor.hpp"

void attn_online_row(const Tensor4D& Q,
                     const Tensor4D& K,
                     const Tensor4D& V,
                     Tensor4D& O,
                     int b, int h, int i,
                     int Bc,
                     bool causal);
