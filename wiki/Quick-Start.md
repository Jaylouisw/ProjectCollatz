# Quick Start

Get up and running with the Collatz Distributed Network in 5 minutes!

## 🎯 Choose Your Path

| Method | Best For | Time to Start | Features |
|--------|----------|---------------|----------|
| **[Future-Proof Engine](#future-proof-engine)** ⭐ | Anyone | 2 minutes | Auto-everything |
| **[Interactive Launcher](#interactive-launcher)** | Full control | 3 minutes | All features |
| **[Docker](#docker)** | Containers | 1 minute | Isolated |
| **[Direct Worker](#direct-worker)** | Advanced | 5 minutes | Scripting |

---

## 🔮 Future-Proof Engine (Recommended)

*Works on any OS and hardware - automatically adapts to your system*

### 1. One-Command Install

**Windows (PowerShell as Administrator):**
```powershell
iwr -useb https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.ps1 | iex
```

**Linux/macOS:**
```bash
curl -sSL https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.sh | bash
```

### 2. Check Compatibility
```bash
python future_proof_engine.py --info
```

**Expected output:**
```
System Information:
  Platform: Windows 10
  Architecture: AMD64  
  Python: 3.11.5

Component Availability:
  Network Transport: ✓ (IPFSTransport)
  Compute Engine: ✓ (CUDAComputeEngine) 
  Configuration Manager: ✓

  Available Transports: ipfs
  Available Engines: cpu, cuda
```

### 3. Run Quick Test
```bash
python future_proof_engine.py --test
```

**Expected output:**
```
Running basic functionality test...
✓ Configuration loaded: CollatzConfig
Testing compute verification...
✓ Verified range 1-100 in 0.003s using CUDA
✓ Network transport available

Basic functionality test completed!
```

### 4. Start Contributing
```bash
python future_proof_engine.py
```

**You're done!** The system will:
- ✅ Detect your hardware (CPU/GPU) automatically
- ✅ Connect to the IPFS network
- ✅ Start verifying Collatz ranges
- ✅ Submit results with cryptographic proofs

---

## 🌐 Interactive Launcher

*Full-featured menu system with user accounts*

### 1. Install (same as above)
```bash
# Use the same installation commands from Future-Proof section
```

### 2. Start Launcher
```bash
python network_launcher.py
```

### 3. Create Account
```
Main Menu:
  1. Start Worker Node (with account)
  2. Start Worker Node (anonymous)
  3. Start Worker Node (CPU-only)
  4. Create User Account          ← Choose this first
  5. View User Statistics
  6. View Global Leaderboard
  0. Exit

Enter choice: 4
```

Follow prompts to create your username.

### 4. Start Worker
```
Enter choice: 1
```

Select your account and start contributing!

**Benefits:**
- ✅ Persistent identity and credit tracking
- ✅ Global leaderboard recognition  
- ✅ Trust level progression
- ✅ Full network features

---

## 🐳 Docker

*Fastest way to get started with containers*

### 1. Pull and Run
```bash
docker pull jaylouisw/collatz-network:latest
docker run -it jaylouisw/collatz-network
```

### 2. That's It!
The container will automatically:
- Start the network launcher
- Guide you through account creation  
- Begin contributing to the network

### Advanced Docker Usage
```bash
# Run in background
docker run -d --name collatz-worker jaylouisw/collatz-network python future_proof_engine.py

# With persistent data
docker run -it -v ./collatz-data:/app/data jaylouisw/collatz-network

# Multiple workers
docker-compose up -d
```

---

## ⚡ Direct Worker (Advanced)

*Command-line interface for automation and scripting*

### 1. Install (same as above)

### 2. Create Account
```bash
python -c "
from user_account import UserAccountManager
manager = UserAccountManager() 
manager.create_account('your_username')
"
```

### 3. Start Worker
```bash
python distributed_collatz.py --user-key ./keys/your_username_private_key.pem
```

### Command Options
```bash
# Anonymous mode (no account needed)
python distributed_collatz.py --anonymous

# CPU-only mode
python distributed_collatz.py --cpu-only --user-key ./keys/your_key.pem

# Custom worker name
python distributed_collatz.py --worker-name server-01 --user-key ./keys/your_key.pem

# Multiple workers
for i in {1..4}; do
    python distributed_collatz.py --user-key ./keys/your_key.pem --worker-name worker-$i &
done
```

---

## 🔍 What Happens Next?

### Network Connection
```
2025-10-27 15:30:22 - INFO - Initializing Future-Proof Collatz Engine
2025-10-27 15:30:23 - INFO - Initialized network transport: IPFSTransport  
2025-10-27 15:30:24 - INFO - Connected to network as node: 12D3KooW...
```

### Work Assignment
```
2025-10-27 15:30:25 - INFO - Starting distributed computation...
2025-10-27 15:30:26 - INFO - Claimed work range: 1000001-1010000
2025-10-27 15:30:26 - INFO - Verifying range 1000001-1010000
```

### Verification and Submission
```
2025-10-27 15:30:27 - INFO - Range verified: 1000001-1010000 (1.2s, CUDA)
2025-10-27 15:30:28 - INFO - Submitting cryptographic proof...
2025-10-27 15:30:29 - INFO - Proof accepted, trust +10 (total: 110)
```

### Continuous Progress
```
2025-10-27 15:30:30 - INFO - Claimed work range: 1010001-1020000
2025-10-27 15:30:31 - INFO - Verifying range 1010001-1020000
```

The system will continue automatically, contributing to the global verification effort!

---

## 📊 Monitor Your Progress

### Real-Time Statistics
```bash
# View your personal stats
python network_launcher.py
# Choose option 5: View User Statistics

# View global leaderboard
python network_launcher.py  
# Choose option 6: View Global Leaderboard
```

### Performance Monitoring
```bash
# System diagnostics
python network_launcher.py
# Choose option 10: Run System Diagnostics

# IPFS network status
python network_launcher.py
# Choose option 11: Check IPFS Status
```

### Web Dashboard
Visit the [Global Leaderboard](https://ipfs.io/ipns/collatz-leaderboard) to see:
- Top contributors worldwide
- Network statistics and health
- Your ranking and progress

---

## 🔧 Performance Tips

### GPU Acceleration
- **NVIDIA**: Install [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
- **AMD**: Install [ROCm](https://rocmdocs.amd.com/en/latest/Installation_Guide/Installation-Guide.html) (Linux)
- **Intel**: Support coming soon
- **Apple**: Metal support ready

### System Optimization
```bash
# Check GPU status
nvidia-smi        # NVIDIA
rocm-smi         # AMD

# Monitor resources
htop             # CPU/Memory
iotop            # Disk I/O
```

### Network Optimization
```bash
# IPFS performance tuning
ipfs config --json Datastore.GCPeriod '"1h"'
ipfs config --json Swarm.ConnMgr.HighWater 200
ipfs config --json Swarm.ConnMgr.LowWater 50
```

---

## ❓ Common Issues

### "IPFS daemon not running"
```bash
# Start IPFS daemon
ipfs daemon

# Or in background
ipfs daemon &
```

### "No GPU detected"  
```bash
# Check GPU drivers
nvidia-smi        # Should show GPU info
python -c "import torch; print(torch.cuda.is_available())"  # Should print True
```

### "No work available"
```bash
# Wait 5-10 minutes for work generation
# Or generate work manually:
python network_launcher.py
# Choose option 7: Generate Work Ranges
```

### "Permission denied"
```bash
# Fix file permissions
chmod +x *.py
chmod +x install.sh

# On Linux, add user to groups
sudo usermod -a -G docker $USER
sudo usermod -a -G render $USER  # For GPU access
```

---

## 🎉 You're Contributing!

**Congratulations!** You're now part of the global effort to solve the Collatz Conjecture!

### What You're Doing
- **Verifying** ranges of numbers follow the Collatz sequence to 1
- **Creating** permanent cryptographic proofs of your work
- **Building** the most comprehensive verification of the conjecture ever attempted
- **Contributing** to mathematical history and scientific knowledge

### Next Steps
1. **Monitor Progress**: Check your stats and ranking
2. **Scale Up**: Add more workers or upgrade hardware  
3. **Get Involved**: Join discussions and contribute to development
4. **Spread the Word**: Tell others about the project

### Need Help?
- **[Troubleshooting](Troubleshooting)** - Common issues and solutions
- **[User Guide](User-Guide)** - Detailed usage instructions
- **[FAQ](FAQ)** - Frequently asked questions
- **[GitHub Issues](https://github.com/Jaylouisw/ProjectCollatz/issues)** - Report bugs

**Welcome to the Collatz Distributed Network community!** 🚀

*Together, we're tackling one of mathematics' greatest unsolved problems!*