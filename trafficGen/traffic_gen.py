#!/usr/bin/env python3
import subprocess
import time
import argparse
import threading
import shutil
import sys
import os

# colours for the visuals
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
CYAN = '\033[96m'
RESET = '\033[0m'

def check_tools():
    """Verifies all required tools are installed."""
    missing = []
    if not shutil.which("iperf3"): missing.append("iperf3")
    if not shutil.which("sockperf"): missing.append("sockperf")
    if not shutil.which("hping3"): missing.append("hping3")
    
    if missing:
        print(f"{RED}[Error] Missing tools: {', '.join(missing)}{RESET}")
        print(f"Run: {YELLOW}./setup.sh{RESET}")
        sys.exit(1)

def run_command(cmd, label, capture=True):
    """Helper to run commands and handle output."""
    print(f"{CYAN}[Starting] {label}...{RESET}")
    try:
        if capture:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                print(f"{RED}[Failed] {label}{RESET}\n{result.stderr}")
                return None
            print(f"{GREEN}[Done] {label}{RESET}")
            return result.stdout
        else:
            # For flood/stress tests where we don't need output capture
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "Started"
    except Exception as e:
        print(f"{RED}[Error] {label}: {e}{RESET}")
        return None

# traffic workload defs

def workload_bulk(ip, duration):
    """
    1. BULK TRAFFIC (Throughput) - iPerf3
    """
    cmd = ["iperf3", "-c", ip, "-t", str(duration), "-P", "4"]
    return run_command(cmd, "Bulk Traffic (iPerf3)")

def workload_short(ip, duration):
    """
    2. SHORT TRAFFIC (Latency) - Sockperf
    """
    cmd = [
        "sockperf", "under-load", "-i", ip, "--tcp",
        "-t", str(duration), "--mps", "50" 
    ]
    return run_command(cmd, "Short Traffic (Sockperf)")

def workload_flood(ip, duration):
    """
    3. FLOOD TRAFFIC (Stress) - hping3 (Requires Sudo)
    """
    if os.geteuid() != 0:
        print(f"{RED}Error: Flood requires sudo!{RESET}")
        return None
    
    cmd = ["timeout", str(duration), "hping3", "--flood", "-S", "-p", "80", "-d", "120", ip]
    run_command(cmd, "Flood Traffic (hping3)", capture=False)
    return "Flood Complete"

# mixed trarfic simulation

def run_mixed_bulk(ip, duration):
    """
    4. MIXED: BULK + SHORT
    """
    print(f"\n{YELLOW}=== MIXED MODE: BULK + SHORT ==={RESET}")
    results = {}
    
    def t_bulk():
        results['bulk'] = workload_bulk(ip, duration)
    
    def t_short():
        time.sleep(2) 
        results['short'] = workload_short(ip, duration - 2)

    t1 = threading.Thread(target=t_bulk)
    t2 = threading.Thread(target=t_short)
    t1.start(); t2.start()
    t1.join(); t2.join()
    
    print(f"\n{CYAN}>>> Bulk Result:{RESET}\n{results.get('bulk')}")
    print(f"\n{CYAN}>>> Short Result:{RESET}\n{results.get('short')}")

def run_mixed_flood(ip, duration):
    """
    5. MIXED: FLOOD + SHORT (The "Attack" Simulation)
    """
    print(f"\n{YELLOW}=== MIXED MODE: FLOOD + SHORT ==={RESET}")
    if os.geteuid() != 0:
        print(f"{RED}Error: Flood requires sudo!{RESET}")
        return

    results = {}

    def t_flood():
        cmd = ["timeout", str(duration), "hping3", "--flood", "-S", "-p", "80", ip]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def t_short():
        time.sleep(2) 
        results['short'] = workload_short(ip, duration - 4)

    t1 = threading.Thread(target=t_flood)
    t2 = threading.Thread(target=t_short)
    t1.start(); t2.start()
    t1.join(); t2.join()
    
    print(f"\n{CYAN}>>> Latency during Flood:{RESET}\n{results.get('short')}")


def main():
    parser = argparse.ArgumentParser(description="eBPF Project Traffic Generator")
    parser.add_argument("ip", help="Target IP Address")
    parser.add_argument("--mode", choices=['bulk', 'short', 'flood', 'mixed_bulk', 'mixed_flood', 'all'], required=True, help="Experiment Mode")
    parser.add_argument("--duration", type=int, default=10, help="Duration in seconds")
    
    args = parser.parse_args()
    check_tools()

    if args.mode == 'bulk':
        print(workload_bulk(args.ip, args.duration))
    elif args.mode == 'short':
        print(workload_short(args.ip, args.duration))
    elif args.mode == 'flood':
        workload_flood(args.ip, args.duration)
    elif args.mode == 'mixed_bulk':
        run_mixed_bulk(args.ip, args.duration)
    elif args.mode == 'mixed_flood':
        run_mixed_flood(args.ip, args.duration)
    elif args.mode == 'all':
        print(workload_bulk(args.ip, args.duration))
        time.sleep(2)
        print(workload_short(args.ip, args.duration))
        time.sleep(2)
        workload_flood(args.ip, args.duration)
        time.sleep(2)
        run_mixed_bulk(args.ip, args.duration)
        time.sleep(2)
        run_mixed_flood(args.ip, args.duration)

if __name__ == "__main__":
    main()
