#!/usr/bin/env python3

from bcc import BPF
import subprocess
import time
import sys
import os

DEVICE = "ens33"
XDP_OBJ = "xdp.o"
TC_OBJ = "tc.o"

THRESH_TC = 5000
THRESH_XDP = 30000

prog = """
#include <uapi/linux/bpf.h>

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

def run_cmd(cmd):
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

class AdaptiveOrchestrator:

    def __init__(self):
        self.state = None
        self.last_rx = self.get_rx()
        
        self.b = BPF(text=prog)
        self.sock_fn = self.b.load_func("count_packets", BPF.SOCKET_FILTER)
        
        self.cleanup()

    def get_rx(self):
        try:
            with open(f"/sys/class/net/{DEVICE}/statistics/rx_packets", "r") as f:
                return int(f.read().strip())
        except:
            return 0

    def cleanup(self):
        run_cmd(f"ip link set dev {DEVICE} xdp off")
        run_cmd(f"tc qdisc del dev {DEVICE} clsact")
        
        try:
            self.b.remove_raw_socket(DEVICE)
        except:
            pass

    def set_mode(self, mode):
        if self.state == mode:
            return
            
        print(f"\n[Switchover] Traffic adapting. Moving to {mode} hook...")
        self.cleanup()
        
        if mode == "SOCKET":
            self.b.attach_raw_socket(self.sock_fn, DEVICE)
            
        elif mode == "TC":
            run_cmd(f"tc qdisc add dev {DEVICE} clsact")
            run_cmd(f"tc filter add dev {DEVICE} ingress bpf obj {TC_OBJ} sec tc da")
            
        elif mode == "XDP":
            run_cmd(f"ip link set dev {DEVICE} xdp obj {XDP_OBJ} sec xdp_static")
            
        self.state = mode

    def monitor(self):
        print(f"Monitoring traffic on {DEVICE}...")
        self.set_mode("SOCKET")
        
        try:
            while True:
                time.sleep(1)
                
                curr_rx = self.get_rx()
                pps = curr_rx - self.last_rx
                self.last_rx = curr_rx
                
                print(f"Current Traffic: {pps} PPS | Active Hook: {self.state}", end="\r")

                if pps > THRESH_XDP:
                    self.set_mode("XDP")
                elif pps > THRESH_TC:
                    self.set_mode("TC")
                else:
                    self.set_mode("SOCKET")
                    
        except KeyboardInterrupt:
            self.cleanup()

if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("Run with sudo!")
        
    AdaptiveOrchestrator().monitor()
