# Algorithm Explanation

Tensor shapes:

```text
Q, K, V, O: B x H x L x Dh
```

Indices:

```text
b = batch
h = head
i = query token
j = key/value token
d = feature dimension
```

Formula:

```text
S[i,j] = dot(Q[i], K[j]) / sqrt(Dh)
P[i,j] = softmax(S[i,:])
O[i,d] = sum_j P[i,j] * V[j,d]
```

Time complexity:

```text
O(B * H * L^2 * Dh)
```

Co `L` query rows, moi query attend toi `L` keys, moi pair can dot product
do dai `Dh`, roi nhan voi `B` va `H`.

Naive memory:

```text
O(B * H * L^2)
```

Vi full attention luu `S[L,L]` va `P[L,L]` cho moi batch/head.

## Versions

- `attn_full`: serial oracle, luu full S va P.
- `attn_row`: serial row-wise, chi luu `scores[L]`.
- `attn_online_row`: tinh mot row bang blocked online softmax.
- `attn_omp_row`: OpenMP row-wise.
- `attn_omp_online`: OpenMP + online softmax.
- `attn_mpi_online`: MPI chia rows, moi rank tinh rows cua minh bang OpenMP.

## Online Softmax

Online softmax giu:

```text
m   = running max
l   = running denominator
out = running numerator/output accumulator
```

Khi block moi co max lon hon:

```text
m_new = max(m, m_block)
alpha = exp(m - m_new)
l_new = alpha * l + sum(exp(score - m_new))
out_new = alpha * out + sum(exp(score - m_new) * V)
```

`alpha` can thiet vi cac gia tri cu da duoc normalize theo max cu `m`.
Khi max doi thanh `m_new`, phai rescale lai denominator va output accumulator.
