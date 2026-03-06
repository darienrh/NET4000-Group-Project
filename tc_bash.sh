INTERFACE = "enp0s3"
tc qdisc del dev $INTERFACE clsat 2>/dev/null

tc qdisc add dev $INTERFACE clsat

tc filter add dev $INTERFACE ingress bpf da obj tc_prog.o sec tc

echo "eBPF program attached to $INTERFACE ingress"
