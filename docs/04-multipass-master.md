# 04 - Multipass Master

Use this path when UTM GUI is annoying and the master should be managed by CLI.

## Host Setup

On macOS:

```bash
brew install --cask multipass
multipass networks
multipass set local.bridged-network=en0
```

Use `en0` for Wi-Fi unless the group is using a USB-C Ethernet adapter.

## Launch Master

From this repo on macOS:

```bash
multipass launch lts \
  --name pp-master \
  --cpus 4 \
  --memory 4G \
  --disk 40G \
  --bridged \
  --cloud-init multipass/cloud-init-master.yaml
```

Wait for cloud-init:

```bash
multipass exec pp-master -- cloud-init status --wait
```

Copy the setup repo into the VM:

```bash
tar --exclude .git --exclude configs/cluster.env -czf /tmp/parallel-macbook-cluster-setup.tgz .
multipass transfer /tmp/parallel-macbook-cluster-setup.tgz pp-master:/home/ubuntu/
multipass exec pp-master -- sudo -u mpiuser tar -xzf /home/ubuntu/parallel-macbook-cluster-setup.tgz -C /home/mpiuser
```

Prepare `/shared/mpi`:

```bash
multipass exec pp-master -- sudo -u mpiuser bash /home/mpiuser/parallel-macbook-cluster-setup/scripts/master_prepare_shared_mpi.sh
multipass exec pp-master -- sudo -u mpiuser bash /home/mpiuser/parallel-macbook-cluster-setup/scripts/run_local_smoke.sh /shared/mpi
```

Collect master info:

```bash
multipass exec pp-master -- sudo -u mpiuser bash /home/mpiuser/parallel-macbook-cluster-setup/scripts/collect_node_info.sh
```

The IPv4 address should be in the same LAN as node1/node2, for example
`192.168.31.x`.

