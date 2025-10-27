# Troubleshooting Guide

Having issues with the Collatz Distributed Network? This comprehensive guide covers solutions to common problems and diagnostic procedures.

## 🚨 Quick Problem Resolution

### Emergency Checklist
If nothing is working, run through this checklist:

```bash
# 1. Check Python version and basic dependencies
python --version          # Should be 3.8 or higher
pip list | grep -E "(ipfs|torch|cryptography)"

# 2. Verify IPFS daemon is running
ipfs swarm peers | wc -l  # Should show connected peers (>0)

# 3. Test basic network connectivity
ping 8.8.8.8              # Internet connectivity
ipfs id                   # IPFS node identity

# 4. Run system diagnostics
python run_diagnostics.py
```

### Most Common Issues (90% of problems)

| Problem | Quick Fix | Time |
|---------|-----------|------|
| **"IPFS daemon not running"** | `ipfs daemon &` | 30s |
| **"No GPU detected"** | Install CUDA drivers | 10m |
| **"Import errors"** | `pip install -r requirements_distributed.txt` | 2m |
| **"No work available"** | Wait 5 minutes, network generates work | 5m |
| **"Permission denied"** | `chmod +x *.py` | 10s |

---

## 🔧 Installation Issues

### Python Environment Problems

#### "Python version not supported"
```bash
# Check current version
python --version

# If < 3.8, install newer Python
# Ubuntu/Debian:
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# Create new virtual environment
python3.11 -m venv collatz-env
source collatz-env/bin/activate
```

#### "pip install fails with compilation errors"
```bash
# Install system dependencies first
# Ubuntu/Debian:
sudo apt install build-essential python3-dev libffi-dev libssl-dev

# CentOS/RHEL:
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel openssl-devel libffi-devel

# Windows:
# Install Microsoft C++ Build Tools from:
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Then retry pip install
pip install -r requirements_distributed.txt
```

#### "ModuleNotFoundError" after installation
```bash
# Verify virtual environment is activated
which python                    # Should point to your venv
pip list | grep collatz         # Should show installed packages

# If packages missing, reinstall
pip install --force-reinstall -r requirements_distributed.txt

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### IPFS Installation Issues

#### "IPFS command not found"
```bash
# Verify IPFS installation
which ipfs

# If not found, install IPFS
# Method 1: Direct download
wget https://github.com/ipfs/kubo/releases/latest/download/kubo_linux-amd64.tar.gz
tar -xzf kubo_linux-amd64.tar.gz
sudo mv kubo/ipfs /usr/local/bin/

# Method 2: Package manager
# Ubuntu:
sudo snap install ipfs
# macOS:
brew install ipfs
```

#### "IPFS init fails"
```bash
# Clean IPFS directory if corrupted
rm -rf ~/.ipfs
ipfs init

# If still fails, check permissions
ls -la ~/.ipfs
chmod -R 755 ~/.ipfs
```

#### "IPFS daemon won't start"
```bash
# Check if already running
ipfs swarm peers

# If running but not responsive, restart
pkill ipfs
ipfs daemon &

# Check logs for errors
tail -f ~/.ipfs/logs/events.log
```

### GPU Setup Issues

#### NVIDIA CUDA Problems
```bash
# Check GPU detection
nvidia-smi

# If command not found, install drivers
# Ubuntu:
sudo apt update
sudo apt install nvidia-driver-525  # Latest stable
sudo reboot

# Check CUDA installation  
nvcc --version

# If not found, install CUDA toolkit
# Download from: https://developer.nvidia.com/cuda-downloads
# Follow platform-specific instructions

# Verify PyTorch CUDA support
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python -c "import torch; print(f'CUDA devices: {torch.cuda.device_count()}')"
```

#### AMD ROCm Problems (Linux)
```bash
# Check GPU detection
rocm-smi

# Install ROCm (Ubuntu)
wget -qO - https://repo.radeon.com/rocm/rocm.gpg.key | sudo apt-key add -
echo 'deb [arch=amd64] https://repo.radeon.com/rocm/apt/debian/ ubuntu main' | sudo tee /etc/apt/sources.list.d/rocm.list
sudo apt update
sudo apt install rocm-dkms

# Add user to render group
sudo usermod -a -G render $USER
sudo reboot

# Verify installation
python -c "import torch; print(f'ROCm available: {torch.cuda.is_available()}')"
```

---

## 🌐 Network Connectivity Issues

### IPFS Network Problems

#### "No peers connected"
```bash
# Check peer count
ipfs swarm peers | wc -l

# If 0 peers, try manual connections
ipfs swarm connect /ip4/104.131.131.82/tcp/4001/p2p/QmaCpDMGvV2BGHeYERUEnRQAwe3N8SzbUtfsmvsqQLuvuJ

# Enable mdns discovery
ipfs config --json Discovery.MDNS.Enabled true
ipfs config --json Discovery.MDNS.Interval 10

# Restart daemon
pkill ipfs
ipfs daemon &
```

#### "DHT queries failing"
```bash
# Check DHT mode
ipfs config Routing.Type

# Should be "dht" for full node or "dhtclient" for light client
ipfs config Routing.Type dht
ipfs daemon &

# Test DHT functionality
ipfs dht findpeer QmaCpDMGvV2BGHeYERUEnRQAwe3N8SzbUtfsmvsqQLuvuJ
```

#### "Firewall blocking IPFS"
```bash
# Check IPFS ports (default 4001)
netstat -tulpn | grep 4001

# Open firewall ports
# Ubuntu (ufw):
sudo ufw allow 4001
sudo ufw reload

# CentOS/RHEL (firewalld):
sudo firewall-cmd --permanent --add-port=4001/tcp
sudo firewall-cmd --reload

# Check if ports are accessible
telnet your.server.ip 4001
```

### Network Transport Failures

#### "IPFSTransport initialization failed"
```python
# Debug IPFS transport issues
python -c "
from ipfs_coordinator import IPFSCoordinator
coordinator = IPFSCoordinator()
try:
    coordinator.connect()
    print('IPFS transport working')
except Exception as e:
    print(f'IPFS transport error: {e}')
"
```

#### "Work coordination failures"
```bash
# Check network coordination logs
tail -f realtime_stats.json

# Verify work generation is running
python -c "
from network_launcher import generate_work_ranges
generate_work_ranges(count=10)
print('Work generation test completed')
"
```

---

## ⚡ Performance Issues

### Slow Computation Speed

#### "GPU not being used"
```python
# Check GPU utilization during computation
# Terminal 1: Start monitoring
nvidia-smi -l 1  # Update every second

# Terminal 2: Start computation
python future_proof_engine.py

# GPU utilization should be >80% during computation
# If 0%, check CUDA installation and PyTorch version
```

#### "CPU maxed out but slow performance"
```python
# Check if using all CPU cores
import psutil
print(f"CPU cores: {psutil.cpu_count()}")
print(f"CPU usage: {psutil.cpu_percent(interval=1)}")

# Monitor during computation - should use most cores
```

#### "Memory issues with large ranges"
```bash
# Monitor memory usage
free -h
htop

# If running out of memory, reduce batch sizes
python -c "
from config_manager import ConfigManager
config = ConfigManager()
config.set('computation.batch_size', 1000)  # Reduce from default
config.save()
"
```

### Network Performance Issues

#### "Slow IPFS operations"
```bash
# Optimize IPFS configuration
ipfs config --json Datastore.StorageMax '"10GB"'
ipfs config --json Datastore.GCPeriod '"1h"'
ipfs config --json Swarm.ConnMgr.HighWater 200
ipfs config --json Swarm.ConnMgr.LowWater 50

# Enable experimental features
ipfs config --json Experimental.AcceleratedDHTClient true
ipfs config --json Experimental.Libp2pStreamMounting true

# Restart daemon
pkill ipfs
ipfs daemon &
```

#### "High bandwidth usage"
```bash
# Monitor network traffic
iftop              # Linux
nettop             # macOS

# Limit IPFS bandwidth
ipfs config --json Swarm.DisableBandwidthMetrics false
ipfs config Swarm.EnableRelayHop false

# Set bandwidth limits (bytes per second)
ipfs config --json Swarm.BandwidthLimits.RateIn '"10MB"'
ipfs config --json Swarm.BandwidthLimits.RateOut '"5MB"'
```

---

## 🔐 Security & Trust Issues

### Cryptographic Errors

#### "Invalid signature errors"
```bash
# Check system time (affects signature validity)
date
# Should be within 5 minutes of actual time

# Sync system time
sudo ntpdate -s time.nist.gov  # Linux
# Windows: Settings > Time & Language > Sync

# Regenerate keys if still failing
python -c "
from user_account import UserAccountManager
manager = UserAccountManager()
manager.regenerate_keys('your_username')
"
```

#### "Trust level not increasing"
```python
# Check trust calculation
python -c "
from trust_system import TrustCalculator
from user_account import UserAccountManager

manager = UserAccountManager()
account = manager.get_account('your_username')
trust = TrustCalculator()

print(f'Current trust: {account.trust_level}')
print(f'Verified work: {account.verified_work_count}')
print(f'Total submissions: {account.total_submissions}')
print(f'Success rate: {account.verified_work_count/account.total_submissions:.2%}')
"
```

### Account Issues

#### "Account not found"
```bash
# List existing accounts
ls -la keys/
python -c "
from user_account import UserAccountManager
manager = UserAccountManager()
accounts = manager.list_accounts()
print('Available accounts:', accounts)
"

# Create new account if needed
python -c "
from user_account import UserAccountManager
manager = UserAccountManager()
manager.create_account('your_new_username')
"
```

#### "Key file permissions"
```bash
# Fix key file permissions
chmod 600 keys/*.pem
chmod 755 keys/

# Check ownership
ls -la keys/
# Should be owned by your user account
```

---

## 🐛 Application Errors

### Common Error Messages

#### "ConnectionError: Unable to connect to IPFS"
```bash
# Solution 1: Start IPFS daemon
ipfs daemon &

# Solution 2: Check IPFS API port
ipfs config Addresses.API
# Should show /ip4/127.0.0.1/tcp/5001

# Solution 3: Reset IPFS configuration
ipfs config --json API.HTTPHeaders.Access-Control-Allow-Origin '["http://127.0.0.1:5001", "https://webui.ipfs.io"]'
```

#### "WorkClaimError: No work available"
```python
# Generate more work ranges
python -c "
from distributed_collatz import generate_work_ranges
generate_work_ranges(count=100, range_size=10000)
print('Generated 100 new work ranges')
"

# Check work queue status
python -c "
from ipfs_coordinator import IPFSCoordinator
coordinator = IPFSCoordinator()
work_count = coordinator.get_available_work_count()
print(f'Available work ranges: {work_count}')
"
```

#### "ComputeError: CUDA out of memory"
```python
# Reduce batch size
python -c "
from config_manager import ConfigManager
config = ConfigManager()
config.set('cuda.batch_size', 1000)  # Reduce from default 10000
config.set('cuda.memory_fraction', 0.8)  # Use 80% of GPU memory
config.save()
print('Reduced CUDA memory usage settings')
"

# Clear GPU memory
python -c "
import torch
torch.cuda.empty_cache()
print('Cleared GPU memory cache')
"
```

### Debug Mode Diagnostics

#### Enable detailed logging
```python
# Create debug configuration
python -c "
from config_manager import ConfigManager
config = ConfigManager()
config.set('logging.level', 'DEBUG')
config.set('logging.file', 'debug.log')
config.save()
"

# Run with debug logging
python future_proof_engine.py --debug
# Check debug.log for detailed information
```

#### Performance profiling
```bash
# Profile CPU usage
python -m cProfile -o profile_output.prof future_proof_engine.py

# Analyze profile
python -c "
import pstats
stats = pstats.Stats('profile_output.prof')
stats.sort_stats('cumulative')
stats.print_stats(20)
"

# Profile memory usage
python -m memory_profiler future_proof_engine.py
```

---

## 🔍 System Diagnostics

### Automated Diagnosis
```bash
# Full system diagnostic
python run_diagnostics.py --comprehensive

# Quick health check
python run_diagnostics.py --quick

# Network-specific diagnostics
python run_diagnostics.py --network-only
```

### Manual System Checks

#### Hardware verification
```bash
# CPU information
lscpu                          # Linux
sysctl -n machdep.cpu.brand_string  # macOS

# Memory information
free -h                        # Linux
vm_stat                        # macOS

# GPU information
nvidia-smi                     # NVIDIA
rocm-smi                       # AMD
system_profiler SPDisplaysDataType  # macOS
```

#### Network diagnostics
```bash
# Internet connectivity
ping -c 4 8.8.8.8

# DNS resolution
nslookup github.com

# IPFS network health
ipfs swarm peers | head -10
ipfs bitswap stat
ipfs repo stat
```

#### Storage space check
```bash
# Available disk space
df -h

# IPFS storage usage
ipfs repo stat

# Project directory size
du -sh .
```

---

## 📞 Getting Help

### Self-Service Resources

#### Log Analysis
```bash
# Check application logs
tail -f error_log.json
tail -f realtime_stats.json

# IPFS logs
tail -f ~/.ipfs/logs/events.log

# System logs
journalctl -u ipfs --since "1 hour ago"  # Linux systemd
```

#### Configuration Validation
```bash
# Validate JSON configuration files
python -m json.tool collatz_config.json
python -m json.tool autotuner_state.json

# Check configuration integrity
python -c "
from config_manager import ConfigManager
config = ConfigManager()
config.validate()
print('Configuration is valid')
"
```

### Community Support

#### Before asking for help, provide:
1. **System Information**:
   ```bash
   python --version
   uname -a  # Linux/macOS
   systeminfo | findstr /B /C:"OS Name" /C:"OS Version"  # Windows
   ```

2. **Error Messages**: Full error text, not screenshots
3. **Log Files**: Recent entries from error_log.json
4. **Configuration**: Output of `python run_diagnostics.py --quick`

#### Support Channels
- **GitHub Issues**: Bug reports and feature requests
- **Discord**: Real-time community help
- **Email**: Critical issues to support@collatz-network.org

#### Bug Report Template
```markdown
**System Information:**
- OS: Ubuntu 22.04
- Python: 3.11.5
- GPU: NVIDIA RTX 4080
- IPFS: 0.23.0

**Problem Description:**
[Clear description of what went wrong]

**Steps to Reproduce:**
1. Run `python future_proof_engine.py`
2. Select option 1
3. Error appears after 30 seconds

**Expected Behavior:**
[What should have happened]

**Error Messages:**
```
[Full error text here]
```

**Diagnostic Output:**
```
[Output of `python run_diagnostics.py --quick`]
```
```

---

## 🚀 Advanced Troubleshooting

### Custom Debugging Scripts

#### Network connectivity test
```python
# save as test_network.py
import asyncio
from ipfs_coordinator import IPFSCoordinator

async def test_network():
    coordinator = IPFSCoordinator()
    
    try:
        # Test basic connection
        await coordinator.connect()
        print("✓ IPFS connection successful")
        
        # Test peer discovery
        peers = await coordinator.get_peer_count()
        print(f"✓ Connected peers: {peers}")
        
        # Test work coordination
        work = await coordinator.get_available_work()
        print(f"✓ Available work ranges: {len(work)}")
        
        print("Network connectivity test PASSED")
        
    except Exception as e:
        print(f"✗ Network test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_network())
```

#### GPU performance test
```python
# save as test_gpu.py
import time
import torch
from compute_engine import CUDAComputeEngine

def test_gpu_performance():
    if not torch.cuda.is_available():
        print("✗ CUDA not available")
        return False
        
    engine = CUDAComputeEngine()
    
    # Test small range
    start_time = time.time()
    result = engine.verify_range(1, 10000)
    small_time = time.time() - start_time
    
    print(f"✓ Small range (10K): {small_time:.3f}s")
    
    # Test large range
    start_time = time.time()
    result = engine.verify_range(1000000, 1100000)
    large_time = time.time() - start_time
    
    print(f"✓ Large range (100K): {large_time:.3f}s")
    
    # Performance expectations
    if large_time < 1.0:
        print("✓ GPU performance: EXCELLENT")
    elif large_time < 5.0:
        print("✓ GPU performance: GOOD")
    elif large_time < 15.0:
        print("⚠ GPU performance: ACCEPTABLE")
    else:
        print("✗ GPU performance: POOR - check drivers/hardware")
        
    return True

if __name__ == "__main__":
    test_gpu_performance()
```

### Recovery Procedures

#### Complete system reset
```bash
# Backup important data
cp -r keys/ keys_backup/
cp user_accounts.json user_accounts_backup.json

# Clean IPFS
ipfs repo gc
pkill ipfs
rm -rf ~/.ipfs
ipfs init

# Reset configuration
rm -f collatz_config.json autotuner_state.json optimization_state.json
python -c "
from config_manager import ConfigManager
config = ConfigManager()
config.reset_to_defaults()
config.save()
"

# Restart fresh
ipfs daemon &
python future_proof_engine.py
```

#### Corrupted state recovery
```bash
# Detect corruption
python -c "
import json
try:
    with open('autotuner_state.json') as f:
        json.load(f)
    print('Autotuner state: OK')
except:
    print('Autotuner state: CORRUPTED')
"

# Reset corrupted files
rm -f autotuner_state.json optimization_state.json
python -c "
from optimization_state import OptimizationState
state = OptimizationState()
state.reset()
state.save()
print('Reset optimization state')
"
```

---

**Remember**: Most issues are caused by environment setup problems. Follow the installation guide carefully, and don't hesitate to ask for help in our community channels!

*When in doubt, try the automated diagnostics first: `python run_diagnostics.py --comprehensive`*