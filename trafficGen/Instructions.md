# Traffic Generator for Adaptive eBPF Project

This module generates diverse network traffic patterns (Bulk, Short, Flood) to benchmark eBPF hook performance.

## Files
* `traffic_gen.py`: Main script.
* `setup.sh`: Installs dependencies (iperf3, sockperf, hping3).

## Usage
1. Run setup:
   `chmod +x setup.sh && ./setup.sh`
2. Run experiments (requires sudo for flood):
   `sudo python3 traffic_gen.py <TARGET_IP> --mode all --duration 10`

   ## In The Ubuntu VM
   git clone -b main https://github.com/YOUR_USERNAME/YOUR_REPO.git
   cd NET4000-Group-Project (you might have to login first)
   Then,
   `chmod +x setup.sh`
   `chmod +x traffic_gen.py`
   `./setup.sh`

   #TO RUN THE TRAFFIC THE OTHER HOST MUST HAVE IPERF3 SOCKPERF RUNNING
   `iperf3 -s and sockperf server --tcp`

TO RUN `sudo python3 traffic_gen.py <PARTNER_IP> --mode mixed_flood --duration 20`
