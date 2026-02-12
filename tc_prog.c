#include <linux/bpf.h>
#include <linux/pkt_cls.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/in.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

/* * Define a map to store traffic stats.
 * Key: Protocol Type (0: TCP, 1: UDP, 2: ICMP, 3: OTHER)
 * Value: Packet Count
 */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 4);
    __type(key, __u32);
    __type(value, __u64);
} traffic_stats SEC(".maps");

// Indices for our classification
#define IDX_TCP 0
#define IDX_UDP 1
#define IDX_ICMP 2
#define IDX_OTHER 3

/* * Helper to parse the packet and find the IP header.
 * In TC, we work with socket buffers (skb).
 */
static __always_inline int parse_ip_proto(struct __sk_buff *skb) {
    void *data_end = (void *)(long)skb->data_end;
    void *data = (void *)(long)skb->data;
    struct ethhdr *eth = data;

    // Boundary check: Ensure packet is large enough for Ethernet header
    if ((void *)(eth + 1) > data_end)
        return -1;

    // We only care about IPv4 for this example
    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return -1;

    struct iphdr *ip = (void *)(eth + 1);
    
    // Boundary check: Ensure packet is large enough for IP header
    if ((void *)(ip + 1) > data_end)
        return -1;

    return ip->protocol;
}

SEC("tc")
int tc_traffic_monitor(struct __sk_buff *skb) {
    __u32 key = IDX_OTHER;
    __u64 *value;

    int proto = parse_ip_proto(skb);

    // Classify based on IP protocol
    if (proto == IPPROTO_TCP) {
        key = IDX_TCP;
    } else if (proto == IPPROTO_UDP) {
        key = IDX_UDP;
    } else if (proto == IPPROTO_ICMP) {
        key = IDX_ICMP;
    }

    // Look up the map element
    value = bpf_map_lookup_elem(&traffic_stats, &key);
    
    if (value) {
        // Atomic increment to ensure accuracy under high load
        __sync_fetch_and_add(value, 1);
        // If you need byte count: __sync_fetch_and_add(value, skb->len);
    }

    // TC_ACT_OK tells the kernel to proceed with the packet normally
    return TC_ACT_OK;
}

char _license[] SEC("license") = "GPL";