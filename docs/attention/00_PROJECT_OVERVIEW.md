# Hybrid MPI + OpenMP Blocked Online Self-Attention

Project nay khong train Transformer. Project chi tinh kernel inference:

```text
O = softmax(QK^T / sqrt(Dh)) V
Q,K,V,O: B x H x L x Dh
```

Muc tieu la nghien cuu song song hoa tren CPU cluster:

- data decomposition theo query rows
- mapping rows vao MPI ranks
- OpenMP chia local rows cho threads
- communication overhead
- load balancing va granularity
- correctness so voi serial baseline
- speedup va efficiency

Cluster setup cung la mot phan cua bai:

```text
master -> Ubuntu VM on physical machine 1
node1  -> Ubuntu VM on physical machine 2
node2  -> Ubuntu VM on physical machine 3
```

Master duoc tinh toan nhu mot compute node. Demo can thay rank chay tren ca
`master`, `node1`, va `node2`.

## Cau Hoi Hay Gap

Q: Vi sao khong train Transformer?

A: Training can dataset, tokenizer, backward pass, optimizer, many layers.
Project nay tap trung vao self-attention inference kernel de phan tich
parallelization, communication, load balancing, va speedup.

Q: Vi sao CPU cluster thay vi GPU?

A: Mon hoc yeu cau MPI cluster tren may vat ly. CPU cluster lam ro MPI,
OpenMP, mapping, granularity va communication overhead.

Q: Cai gi duoc song song hoa?

A: Query rows. Moi output row doc Q/K/V va ghi vao mot row rieng cua O.

Q: Vi sao khong can lock?

A: Q/K/V read-only. Moi task ghi mot output row khac nhau.
