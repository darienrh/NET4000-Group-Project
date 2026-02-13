#!/usr/bin/python3
from bcc import BPF
import time

# Rafay - Static Socket Implementation
# Interface from VM setup
device = "ens33"

# Simple C program to count packets at the socket layer
prog = """
#include <uapi/linux/bpf.h>
#include <uapi/linux/if_ether.h>
#include <uapi/linux/ip.h>

BPF_ARRAY(packet_count, u64, 1);

int count_packets(struct __sk_buff *skb) {
    int key = 0;
    u64 *val, zero = 0;

    val = packet_count.lookup_or_init(&key, &zero);
    if (val) {
        lock_xadd(val, 1);
    }
    return 0; 
}
"""

# Load the program
b = BPF(text=prog)
function = b.load_func("count_packets", BPF.SOCKET_FILTER)

# Attach to the interface using BCC helper
b.attach_raw_socket(function, device)
print(f"Socket filter attached to {device}, counting packets...")

# Main loop to print stats
try:
    while True:
        time.sleep(1)
        cnt = b["packet_count"][0].value
        print(f"Packets captured: {cnt}")
except KeyboardInterrupt:
    print("\nExiting...")
