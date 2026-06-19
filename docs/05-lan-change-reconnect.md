# Doi Mang LAN Va Ket Noi Lai

Master trong cluster nay khong chi phan cong viec. Neu hostfile co dong
`master slots=...`, OpenMPI se tao rank tren master va master se tinh toan
cung node1/node2.

Trong log 3 may hien tai, rank 0 da chay tren `master`, rank 1 tren `node1`,
rank 2 tren `node2`, nen master dang la compute node that su.

## Khi doi Wi-Fi/LAN

IP LAN co the doi moi lan chuyen sang router/Wi-Fi khac. SSH key thuong khong
doi, tru khi tao lai VM.

Tren tung VM, lay IP moi:

```bash
hostname -I
```

Chon IP cung dai LAN, vi du `192.168.x.x`. Khong dung:

- `192.168.252.2`: day la NAT rieng cua Multipass tren tung may.
- Dia chi bat dau bang `fd...` hoac `fe80...`: day la IPv6.

Moi nguoi gui lai block:

```text
role: master/node1/node2
hostname: ...
LAN IP: ...
ssh status: active/running
```

## Cap Nhat Tren Master

Sua file tren master:

```bash
nano ~/parallel-macbook-cluster-setup/configs/cluster.env
```

Cap nhat:

```bash
MASTER_IP=...
NODE1_IP=...
NODE2_IP=...
LAN_SUBNET=192.168.X.0/24
```

Public key giu nguyen neu VM khong bi tao lai.

Sau do chay tren master VM:

```bash
cd ~/parallel-macbook-cluster-setup
bash scripts/reconnect_after_lan_change.sh
```

Script nay se:

- Cap nhat `/etc/hosts` va SSH config tren master.
- Cap nhat NFS export `/shared/mpi` theo subnet moi.
- Cap nhat `/etc/hosts` tren node1/node2 qua SSH.
- Remount `/shared/mpi` tren node1/node2.
- Chay `mpirun` hello qua 3 may.

Pass khi thay:

```text
Hello from rank 0/3 on master
Hello from rank 1/3 on node1
Hello from rank 2/3 on node2
RECONNECT_READY=YES
```

## Neu Loi

Kiem tra theo thu tu:

```bash
ping node1
ping node2
ssh node1 hostname
ssh node2 hostname
showmount -e master
mount | grep /shared/mpi
```

Neu `ping` tu Mac host duoc nhung tu VM master khong duoc, loi thuong nam o
Bridged networking hoac Wi-Fi/router dang chan VM noi chuyen voi nhau.
