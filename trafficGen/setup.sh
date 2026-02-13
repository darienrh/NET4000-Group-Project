#!/bin/bash
# setup.sh - Install dependencies for Traffic Generator

echo "[Setup] Updating package lists..."
sudo apt-get update

echo "[Setup] Installing iPerf3..."
sudo apt-get install -y iperf3

echo "[Setup] Installing Hping3..."
sudo apt-get install -y hping3

echo "[Setup] Installing Sockperf..."
sudo apt-get install -y sockperf || echo "Warning: Sockperf not found in standard repos. Please install manually or enable universe repo."

echo "[Setup] Complete! You are ready to run traffic_gen.py."
