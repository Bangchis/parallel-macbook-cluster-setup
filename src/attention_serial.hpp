#pragma once

#include "tensor.hpp"

void attn_full(const Tensor4D& Q,
               const Tensor4D& K,
               const Tensor4D& V,
               Tensor4D& O,
               bool causal);

void attn_row(const Tensor4D& Q,
              const Tensor4D& K,
              const Tensor4D& V,
              Tensor4D& O,
              bool causal);
