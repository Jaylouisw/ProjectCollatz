# Deployment Guide v1.0.1

Complete guide for deploying Collatz Distributed Network across all platforms with future-proof compatibility.

## Table of Contents

- [Quick Start](#quick-start)
- [Installation Methods](#installation-methods)
- [Docker Deployment](#docker-deployment)
- [Raspberry Pi Deployment](#raspberry-pi-deployment)
- [Production Deployment](#production-deployment)
- [Multi-Node Setup](#multi-node-setup)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### 🔮 Future-Proof Engine (NEW - Recommended)

**Check system compatibility first:**
```bash
python future_proof_engine.py --info
```

**Run compatibility test:**
```bash
python future_proof_engine.py --test
```

**Start distributed network (auto-detects everything):**
```bash
python future_proof_engine.py
```

**Available on all platforms - works with any hardware configuration!**

### One-Command Install

**Windows (PowerShell as Administrator):**
```powershell
iwr -useb https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.ps1 | iex
```

**Linux / macOS:**
```bash
curl -sSL https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.sh | bash
```

**Docker:**
```bash
docker pull jaylouisw/collatz-network:latest
docker run -it --name collatz-worker jaylouisw/collatz-network
```

---

## Installation Methods

### Method 1: Automated Script (Recommended)

**Linux/macOS:**
```bash
curl -sSL https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.sh | bash
cd ~/collatz-network
./start.sh
```

**Windows:**
```powershell
iwr -useb https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.ps1 | iex
cd $env:USERPROFILE\collatz-network
.\start.ps1
```

**What it does:**
- ✅ Checks Python version (3.8+ required)
- ✅ Clones repository
- ✅ Installs Python dependencies
- ✅ Installs/configures IPFS
- ✅ Creates launch scripts
- ✅ Optional GPU support
- ✅ Optional desktop shortcut (Windows)

### Method 2: Manual Installation

```bash
# 1. Install IPFS
# Download from: https://docs.ipfs.tech/install/
ipfs init

# 2. Clone repository
git clone https://github.com/Jaylouisw/ProjectCollatz.git
cd ProjectCollatz

# 3. Install Python dependencies
pip install -r requirements_distributed.txt

# 4. (Optional) Install GPU support
pip install cupy-cuda12x  # or cupy-cuda11x

# 5. Start IPFS daemon
ipfs daemon &

# 6. Run launcher
python network_launcher.py
```

### Method 3: Using setup.py

```bash
# Install as Python package
git clone https://github.com/Jaylouisw/ProjectCollatz.git
cd ProjectCollatz
pip install -e .

# With GPU support
pip install -e .[gpu]

# Run from anywhere
collatz-network
```

---

## Docker Deployment

### Quick Start

```bash
# Pull image
docker pull jaylouisw/collatz-network:latest

# Run worker node
docker run -d --name collatz-worker \
  -v collatz-ipfs:/home/collatz/.ipfs \
  -v collatz-keys:/app/keys \
  --restart unless-stopped \
  jaylouisw/collatz-network
```

### With User Account

```bash
# Create account locally first
python user_account.py create myusername

# Run with your keys
docker run -d --name collatz-worker \
  -v $PWD/keys:/app/keys:ro \
  -v collatz-ipfs:/home/collatz/.ipfs \
  --restart unless-stopped \
  jaylouisw/collatz-network \
  python distributed_collatz.py --user-key /app/keys/user_myusername_private.pem
```

### Multi-Node Network

```bash
# Using docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Scale workers
docker-compose up -d --scale worker=5

# Stop network
docker-compose down
```

### Build Custom Image

```bash
# Build locally
docker build -t my-collatz-network .

# Build with specific Python version
docker build --build-arg PYTHON_VERSION=3.11 -t my-collatz-network .

# Run custom image
docker run -it my-collatz-network
```

### Docker Hub Publishing

```bash
# Build and tag
docker build -t jaylouisw/collatz-network:latest .
docker build -t jaylouisw/collatz-network:v1.0.0 .

# Push to Docker Hub
docker login
docker push jaylouisw/collatz-network:latest
docker push jaylouisw/collatz-network:v1.0.0
```

---

## Raspberry Pi Deployment

### Method 1: Pre-Built Image (Easiest)

1. **Download image** from [Releases](https://github.com/Jaylouisw/ProjectCollatz/releases)
2. **Write to SD card:**
   ```bash
   # Using Etcher (recommended)
   # Download from: https://www.balena.io/etcher/
   
   # Or using dd
   xzcat collatz-network-pi-*.img.xz | sudo dd of=/dev/sdX bs=4M status=progress
   ```
3. **Configure Wi-Fi (before first boot):**
   - Mount SD card
   - Edit `/boot/wpa_supplicant.conf` with your Wi-Fi credentials
4. **Insert SD card and power on**
5. **SSH into Pi:**
   ```bash
   ssh pi@raspberrypi.local
   # Default password: raspberry (CHANGE THIS!)
   ```

**What happens on first boot:**
- Installs all dependencies (~10 minutes)
- Automatically reboots
- Starts worker node (auto-starts on every boot)

### Method 2: Manual Install on Existing Pi

```bash
# SSH into your Pi
ssh pi@raspberrypi.local

# Run install script
curl -sSL https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.sh | bash

# Start manually
cd ~/collatz-network
./start.sh
```

### Method 3: Build Custom Image

```bash
# On Linux machine
./build-pi-image.sh

# Output: collatz-network-pi-*.img.xz
# Write to SD card using method 1
```

### Pi Configuration

**Create user account:**
```bash
cd ~/collatz-network
python3 user_account.py create pi-worker-1
```

**Configure service to use account:**
```bash
sudo nano /etc/systemd/system/collatz-network.service

# Change ExecStart line to:
ExecStart=/usr/bin/python3 /home/pi/collatz-network/distributed_collatz.py --cpu-only --user-key /home/pi/collatz-network/keys/user_pi-worker-1_private.pem

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart collatz-network
```

**View logs:**
```bash
journalctl -u collatz-network -f
```

**Stop/start service:**
```bash
sudo systemctl stop collatz-network
sudo systemctl start collatz-network
sudo systemctl restart collatz-network
```

### Pi Cluster Setup

For multiple Pis:

1. Write same image to all SD cards
2. Configure unique hostnames:
   ```bash
   sudo raspi-config
   # System Options → Hostname → pi-worker-1
   sudo reboot
   ```
3. Create unique accounts on each:
   ```bash
   python3 user_account.py create pi-worker-1
   python3 user_account.py create pi-worker-2
   # etc.
   ```
4. Configure services with respective keys

---

## Production Deployment

### Pre-Launch Checklist

- [ ] IPFS daemon running on all nodes
- [ ] All nodes can communicate (test with `ipfs swarm peers`)
- [ ] User accounts created for all nodes
- [ ] Keys backed up securely
- [ ] Network initialized with production state
- [ ] At least 3 nodes ready for consensus
- [ ] Monitoring/logging configured

### Production Initialization

**⚠️ ONLY DO THIS ONCE BEFORE LAUNCH! ⚠️**

```bash
python network_launcher.py
# Choose option 11: Initialize for Production
# Type "YES" to confirm
```

This resets the network to 2^71 with a genesis timestamp.

### Launch Sequence

**Coordinator node (first):**
```bash
# Generate initial work
python distributed_collatz.py --generate-work 1000

# Start coordinator
python distributed_collatz.py --user-key ./keys/user_coordinator_private.pem
```

**Worker nodes (after coordinator is running):**
```bash
# Node 1
python distributed_collatz.py --user-key ./keys/user_alice_private.pem

# Node 2
python distributed_collatz.py --user-key ./keys/user_bob_private.pem

# Node 3
python distributed_collatz.py --user-key ./keys/user_charlie_private.pem
```

### Monitoring

**Network statistics:**
```bash
python network_launcher.py
# Option 9: View Network Statistics
```

**User statistics:**
```bash
python user_account.py stats <user_id>
python user_account.py leaderboard
```

**IPFS status:**
```bash
ipfs swarm peers  # Connected peers
ipfs stats bw      # Bandwidth usage
ipfs id            # Your node ID
```

**Logs:**
```bash
# Check error_log.json
cat error_log.json | python -m json.tool

# Real-time stats
cat realtime_stats.json | python -m json.tool
```

---

## Multi-Node Setup

### Same Machine (Testing)

```bash
# Terminal 1: IPFS
ipfs daemon

# Terminal 2: Worker 1
python distributed_collatz.py --user-key ./keys/user_alice_private.pem --name worker1

# Terminal 3: Worker 2
python distributed_collatz.py --user-key ./keys/user_bob_private.pem --name worker2

# Terminal 4: Worker 3
python distributed_collatz.py --user-key ./keys/user_charlie_private.pem --name worker3
```

### Different Machines

On each machine:

```bash
# 1. Install Collatz Network (use install script)
curl -sSL https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.sh | bash

# 2. Start IPFS
ipfs daemon

# 3. Create unique account
python user_account.py create machine-1

# 4. Start worker
python distributed_collatz.py --user-key ./keys/user_machine-1_private.pem
```

**Ensure nodes can find each other:**
```bash
# On node 1, get IPFS ID
ipfs id

# On node 2, connect to node 1
ipfs swarm connect /ip4/<node1-ip>/tcp/4001/p2p/<node1-id>
```

### Cloud Deployment (AWS, Azure, GCP)

**Using Docker:**
```bash
# Pull image
docker pull jaylouisw/collatz-network:latest

# Run with persistent storage
docker run -d \
  --name collatz-worker \
  --restart always \
  -v collatz-ipfs:/home/collatz/.ipfs \
  -v collatz-keys:/app/keys \
  -p 4001:4001 \
  jaylouisw/collatz-network
```

**Security groups/firewall:**
- Open TCP 4001 (IPFS swarm)
- Optional: TCP 5001 (IPFS API - internal only!)
- Optional: TCP 8080 (IPFS gateway)

---

## Troubleshooting

### Single Instance Lock Error

**Problem:** "Another instance of the launcher is already running!"

**Solutions:**
```bash
# 1. Check if actually running
ps aux | grep network_launcher

# 2. If no process found, remove stale lock
# Windows
del %TEMP%\collatz_launcher.lock

# Linux/Mac
rm /tmp/collatz_launcher.lock  # or /var/lock/collatz_launcher.lock
```

### IPFS Connection Issues

**Problem:** Workers can't connect to network

**Solutions:**
```bash
# 1. Check IPFS daemon is running
ipfs id

# 2. Check for peers
ipfs swarm peers

# 3. Restart IPFS daemon
pkill ipfs
ipfs daemon

# 4. Bootstrap to public nodes
ipfs bootstrap add --default
```

### Docker Networking

**Problem:** Containers can't communicate

**Solutions:**
```bash
# 1. Use docker-compose (automatic networking)
docker-compose up -d

# 2. Or create custom network
docker network create collatz-net
docker run --network collatz-net ...

# 3. Check container networking
docker network inspect collatz-net
```

### Raspberry Pi Issues

**Problem:** Pi won't boot or runs slowly

**Solutions:**
- Use Class 10 or better SD card
- Ensure adequate power supply (5V 3A for Pi 4)
- Check SD card for corruption: `sudo fsck /dev/mmcblk0p2`
- Monitor temperature: `vcgencmd measure_temp`

**Problem:** Service won't start

**Solutions:**
```bash
# Check service status
sudo systemctl status collatz-network

# View logs
journalctl -u collatz-network -n 50

# Restart service
sudo systemctl restart collatz-network

# Check dependencies
cd ~/collatz-network
pip3 install -r requirements_distributed.txt
```

### GPU Not Detected

**Problem:** GPU not being used

**Solutions:**
```bash
# 1. Check GPU is recognized
nvidia-smi

# 2. Install correct CuPy version
pip install cupy-cuda12x  # for CUDA 12.x
pip install cupy-cuda11x  # for CUDA 11.x

# 3. Verify CuPy installation
python -c "import cupy; print(cupy.cuda.is_available())"

# 4. Use CPU-only mode as fallback
python distributed_collatz.py --cpu-only
```

---

## Support

- **Documentation:** [DISTRIBUTED.md](DISTRIBUTED.md)
- **Quick Reference:** [DISTRIBUTED_QUICKREF.md](DISTRIBUTED_QUICKREF.md)
- **GitHub Issues:** https://github.com/Jaylouisw/ProjectCollatz/issues
- **Diagnostics:** `python run_diagnostics.py`

---

**Ready to deploy?** Start with the one-command install for your platform!
