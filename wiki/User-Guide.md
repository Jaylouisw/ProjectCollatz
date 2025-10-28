# User Guide

Complete guide for participating in the Collatz Distributed Network.

## 🎯 Getting Started

### Choose Your Path

The Collatz Network offers multiple ways to participate:

| Option | Best For | Complexity | Features |
|--------|----------|------------|----------|
| **[Future-Proof Engine](#future-proof-engine)** | New users, any platform | ⭐ Easy | Auto-configuration, cross-platform |
| **[Interactive Launcher](#interactive-launcher)** | Detailed control | ⭐⭐ Medium | Full features, user accounts |
| **[Direct Worker](#direct-worker-mode)** | Advanced users | ⭐⭐⭐ Advanced | Automation, scripting |
| **[Local Testing](#local-mode)** | Research, testing | ⭐⭐ Medium | Offline, high performance |

---

## 🔮 Future-Proof Engine

*Recommended for all users - works on any system*

### Quick Start

```bash
# Check what your system supports
python future_proof_engine.py --info

# Run a functionality test
python future_proof_engine.py --test

# Start contributing to the network
python future_proof_engine.py
```

### System Information Check

When you run `--info`, you'll see something like:

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

**What This Means:**
- ✅ **Network Transport**: Can connect to the distributed network
- ✅ **Compute Engine**: Can perform Collatz verification
- ✅ **Available Engines**: Shows CPU (always) and GPU (if available)

### Command Options

```bash
# Show system compatibility
python future_proof_engine.py --info

# Test functionality  
python future_proof_engine.py --test

# Force local mode (no network)
python future_proof_engine.py --local

# Custom configuration file
python future_proof_engine.py --config my_config.json

# Specify compute engine
python future_proof_engine.py --compute cuda

# Specify network transport
python future_proof_engine.py --network ipfs
```

### Understanding Output

When running the future-proof engine, you'll see:

```
============================================================
  FUTURE-PROOF DISTRIBUTED COLLATZ ENGINE
============================================================

2025-10-27 15:30:22 - INFO - Initializing Future-Proof Collatz Engine
2025-10-27 15:30:22 - INFO - Loaded configuration version 2.0
2025-10-27 15:30:23 - INFO - Initialized network transport: IPFSTransport
2025-10-27 15:30:23 - INFO - Initialized compute engine: CUDAComputeEngine
2025-10-27 15:30:24 - INFO - Connected to network as node: 12D3KooW...
2025-10-27 15:30:25 - INFO - Starting distributed computation...
2025-10-27 15:30:26 - INFO - Verifying range 1000001-1010000
2025-10-27 15:30:27 - INFO - Range 1000001-1010000 verified successfully
```

**Key Information:**
- **Node ID**: Your unique identifier on the network
- **Range Assignments**: What numbers you're verifying
- **Verification Status**: Success/failure of each range

---

## 🌐 Interactive Launcher

*Full-featured menu system for detailed control*

### Starting the Launcher

```bash
python network_launcher.py
```

### Main Menu

```
======================================================================
    COLLATZ DISTRIBUTED VERIFICATION NETWORK
======================================================================

Main Menu:
  1. Start Worker Node (with account)
  2. Start Worker Node (anonymous)
  3. Start Worker Node (CPU-only)
  4. Create User Account
  5. View User Statistics
  6. View Global Leaderboard
  7. Generate Work Ranges
  8. Update Leaderboard Webpage
  9. View Network Statistics
  10. Run System Diagnostics
  11. Check IPFS Status
  0. Exit

Enter choice:
```

### Menu Options Explained

#### 1. Start Worker Node (with account)
- **Purpose**: Join network with persistent identity
- **Benefits**: Get credit for contributions, build reputation
- **Requirements**: Must have created account first (option 4)

#### 2. Start Worker Node (anonymous)
- **Purpose**: Contribute without creating account
- **Benefits**: Quick participation, no setup required
- **Limitations**: No credit tracking, no reputation building

#### 3. Start Worker Node (CPU-only)
- **Purpose**: Force CPU-only mode
- **Use Cases**: GPU issues, power constraints, testing
- **Performance**: Slower but more stable

#### 4. Create User Account
- **Purpose**: Create persistent identity
- **Process**: Choose username, generates cryptographic keys
- **Storage**: Keys saved in `./keys/` directory

#### 5. View User Statistics
- **Shows**: Your contribution statistics
- **Includes**: Ranges verified, total numbers, verification rate
- **Updates**: Real-time data from network

#### 6. View Global Leaderboard
- **Shows**: Top contributors globally
- **Rankings**: By total contributions and recent activity
- **Updates**: Refreshed periodically from IPFS

#### 7. Generate Work Ranges
- **Purpose**: Create new work for the network
- **Use**: When network runs low on available work
- **Authority**: Only trusted nodes can generate work

#### 8. Update Leaderboard Webpage
- **Purpose**: Refresh public leaderboard display
- **Output**: Updates IPFS-hosted webpage
- **Access**: Public at ipfs.io/ipns/collatz-leaderboard

#### 9. View Network Statistics
- **Shows**: Overall network health and performance
- **Includes**: Active nodes, completion rates, current progress
- **Useful**: Understanding network status

#### 10. Run System Diagnostics
- **Purpose**: Check system health and performance
- **Tests**: IPFS connectivity, GPU status, performance benchmarks
- **Output**: Detailed diagnostic report

#### 11. Check IPFS Status
- **Purpose**: Verify IPFS daemon connectivity
- **Shows**: Connected peers, network status
- **Troubleshooting**: Helps diagnose network issues

---

## ⚡ Direct Worker Mode

*Command-line interface for advanced users*

### Basic Usage

```bash
# Start worker with user account
python distributed_collatz.py --user-key ./keys/username_private_key.pem

# Anonymous worker
python distributed_collatz.py --anonymous

# CPU-only mode
python distributed_collatz.py --cpu-only --user-key ./keys/username_private_key.pem

# Custom worker name
python distributed_collatz.py --worker-name production-node-01 --user-key ./keys/username_private_key.pem
```

### Command Line Options

```bash
# Required (choose one)
--user-key PATH          # Path to private key file
--anonymous              # Run without account

# Optional
--worker-name NAME       # Custom worker identifier
--cpu-only              # Force CPU-only computation
--max-workers N         # Limit parallel workers
--log-level LEVEL       # DEBUG, INFO, WARNING, ERROR
--config PATH           # Custom configuration file
--ipfs-api URL          # Custom IPFS API endpoint
```

### Automation and Scripting

**Basic startup script:**
```bash
#!/bin/bash
# start_collatz_worker.sh

# Set environment
export COLLATZ_LOG_LEVEL=INFO
export COLLATZ_WORKER_NAME=server-01

# Start worker with retry logic
while true; do
    echo "Starting Collatz worker..."
    python distributed_collatz.py --user-key ./keys/myaccount_private_key.pem
    echo "Worker stopped. Restarting in 10 seconds..."
    sleep 10
done
```

**Multi-worker script:**
```bash
#!/bin/bash
# start_multiple_workers.sh

ACCOUNT_KEY="./keys/myaccount_private_key.pem"
WORKER_COUNT=4

for i in $(seq 1 $WORKER_COUNT); do
    echo "Starting worker $i..."
    python distributed_collatz.py \
        --user-key "$ACCOUNT_KEY" \
        --worker-name "worker-$i" \
        --log-level INFO &
done

wait
```

**Docker deployment:**
```bash
# Single worker
docker run -d \
    --name collatz-worker-01 \
    -v ./keys:/app/keys \
    jaylouisw/collatz-network \
    python distributed_collatz.py --user-key /app/keys/myaccount_private_key.pem

# Multiple workers
for i in {1..4}; do
    docker run -d \
        --name collatz-worker-$i \
        -v ./keys:/app/keys \
        jaylouisw/collatz-network \
        python distributed_collatz.py \
            --user-key /app/keys/myaccount_private_key.pem \
            --worker-name docker-worker-$i
done
```

---

## 🖥️ Local Mode

*High-performance single-node verification*

### Legacy Engine

```bash
# Start legacy engine with GPU
python CollatzEngine.py

# CPU-only mode
python CollatzEngine.py --cpu-only

# Custom range
python CollatzEngine.py --start 1000000 --end 2000000
```

### Future-Proof Local Mode

```bash
# Local mode with future-proof engine
python future_proof_engine.py --local

# Benefits over legacy:
# - Cross-platform compatibility
# - Automatic hardware detection
# - Modern configuration system
# - Better error handling
```

### Performance Comparison

| Mode | Speed (numbers/sec) | GPU Support | Network | Use Case |
|------|-------------------|-------------|---------|----------|
| Legacy Engine | ~10B (GPU) | ✅ CUDA | ❌ | Benchmarking |
| Future-Proof Local | ~10B (GPU) | ✅ Multi-GPU | ❌ | Testing |
| Distributed Mode | ~10B (GPU) | ✅ Multi-GPU | ✅ | Production |

---

## 👤 User Accounts

### Creating an Account

**Option 1: Interactive (Recommended)**
```bash
python network_launcher.py
# Choose option 4: Create User Account
# Follow prompts to choose username
```

**Option 2: Direct Creation**
```bash
python -c "
from user_account import UserAccountManager
manager = UserAccountManager()
manager.create_account('your_username')
"
```

**Option 3: Command Line**
```bash
python user_account.py create your_username
```

### Account Structure

When you create an account, the system generates:

```
keys/
├── your_username_private_key.pem    # Private key (keep secret!)
└── your_username_public_key.pem     # Public key (shared with network)
```

**Private Key**: 
- Used to sign your work submissions
- Proves work came from you
- **Never share this file!**

**Public Key**:
- Used by others to verify your signatures
- Shared publicly on the network
- Safe to distribute

### Account Benefits

**With Account:**
- ✅ Persistent identity across sessions
- ✅ Credit for all contributions
- ✅ Reputation building over time
- ✅ Leaderboard recognition
- ✅ Trust level progression
- ✅ Historical contribution tracking

**Anonymous Mode:**
- ❌ No persistent identity
- ❌ No credit for contributions
- ❌ No reputation building
- ❌ Work attributed to "anonymous"
- ✅ Still helps the network
- ✅ Faster to get started

### Managing Multiple Accounts

You can create multiple accounts for different purposes:

```bash
# Personal account
python user_account.py create personal_laptop

# Work account  
python user_account.py create work_desktop

# Testing account
python user_account.py create test_account
```

Switch between accounts:
```bash
# Use personal account
python distributed_collatz.py --user-key ./keys/personal_laptop_private_key.pem

# Use work account
python distributed_collatz.py --user-key ./keys/work_desktop_private_key.pem
```

---

## 📊 Understanding Your Progress

### Trust Levels

Your account progresses through trust levels based on performance:

| Level | Points | Requirements | Benefits |
|-------|---------|-------------|----------|
| **UNTRUSTED** | 0-99 | New account | Limited work assignments |
| **VERIFIED** | 100-499 | 10+ verified ranges | Standard work load |
| **TRUSTED** | 500-999 | Consistent accuracy | Priority assignments |
| **ELITE** | 1000+ | Network leadership | Work generation rights |

### Statistics Tracking

**Individual Stats (Option 5 in launcher):**
```
User Statistics for: your_username
================================

Trust Level: VERIFIED (234 points)
Total Ranges Completed: 45
Total Numbers Verified: 450,000
Average Verification Time: 12.3 seconds
Success Rate: 100.0%
Days Active: 7
Last Activity: 2 hours ago

Recent Activity:
- Range 1,000,001-1,010,000: Verified ✓
- Range 1,010,001-1,020,000: Verified ✓  
- Range 1,020,001-1,030,000: Verified ✓
```

**Global Stats (Option 9 in launcher):**
```
Network Statistics
==================

Active Nodes: 127
Total Numbers Verified: 1,234,567,890
Current Progress: 1,234,567,890
Verification Rate: 45M numbers/second
Network Uptime: 99.7%

Top Contributors (Last 24h):
1. alice_researcher: 12.5M numbers
2. bob_gpu_farm: 8.3M numbers  
3. charlie_datacenter: 6.7M numbers
```

### Performance Optimization

**GPU Performance:**
- Monitor GPU utilization: `nvidia-smi` (NVIDIA) or `rocm-smi` (AMD)
- Optimal GPU memory usage: ~80% utilization
- Temperature monitoring: Keep below 80°C

**CPU Performance:**
- Multi-core utilization: Should use all available cores
- Memory usage: Typically under 1GB per worker
- System load: Aim for load average ≈ CPU core count

**Network Performance:**
- IPFS connectivity: `ipfs swarm peers` should show 20+ peers
- Work assignment latency: Should be under 5 seconds
- Result submission time: Should complete within 30 seconds

---

## 🔍 Monitoring and Troubleshooting

### Real-Time Monitoring

**Console Output:**
```bash
# Standard output shows progress
2025-10-27 15:30:26 - INFO - Verifying range 1000001-1010000
2025-10-27 15:30:27 - INFO - Range verified: 1000001-1010000 (1.2s, CUDA)
2025-10-27 15:30:28 - INFO - Submitting proof for range 1000001-1010000
2025-10-27 15:30:29 - INFO - Proof accepted, trust +10 (total: 234)
```

**Performance Metrics:**
- **Verification Time**: How long each range takes
- **Backend Used**: CPU, CUDA, ROCm, etc.
- **Trust Score**: Your current reputation points
- **Success Rate**: Percentage of successful verifications

### Common Issues and Solutions

#### "No work available"
**Cause**: Network temporarily out of work ranges
**Solution**: Wait 5-10 minutes, or use option 7 to generate work

#### "IPFS connection failed"  
**Cause**: IPFS daemon not running or network issues
**Solution**: 
```bash
# Start IPFS daemon
ipfs daemon

# Check connectivity
ipfs swarm peers
```

#### "GPU not detected"
**Cause**: GPU drivers not installed or not CUDA-compatible
**Solution**:
```bash
# Check GPU status
nvidia-smi  # NVIDIA
rocm-smi    # AMD

# Verify Python can see GPU
python -c "import torch; print(torch.cuda.is_available())"
```

#### "Trust level too low"
**Cause**: New account with limited permissions
**Solution**: Complete more ranges to build trust (automatic)

#### "Verification failed"
**Cause**: Hardware issues or software bugs
**Solution**: 
```bash
# Run diagnostics
python run_diagnostics.py

# Try CPU-only mode
python distributed_collatz.py --cpu-only --user-key ./keys/your_key.pem
```

### Debug Mode

Enable detailed logging:
```bash
# Environment variable
export COLLATZ_LOG_LEVEL=DEBUG

# Or command line
python distributed_collatz.py --log-level DEBUG --user-key ./keys/your_key.pem
```

Debug output includes:
- Network communication details
- GPU memory allocation
- IPFS operations
- Cryptographic operations
- Performance profiling

---

## 🎯 Advanced Usage

### Custom Configuration

Create `collatz_config.json`:
```json
{
  "version": "2.0",
  "network": {
    "transport": "ipfs",
    "connection_timeout": 60,
    "retry_count": 5
  },
  "compute": {
    "engine": "cuda",
    "max_workers": 4,
    "prefer_gpu": true
  },
  "security": {
    "verification_required": true,
    "trust_threshold": 50
  },
  "deployment": {
    "worker_name": "my-custom-worker",
    "log_level": "INFO"
  }
}
```

### Environment Variables

Override config with environment variables:
```bash
# Network settings
export COLLATZ_NETWORK_TRANSPORT=ipfs
export COLLATZ_IPFS_API=/ip4/127.0.0.1/tcp/5001

# Compute settings
export COLLATZ_COMPUTE_ENGINE=cuda
export COLLATZ_MAX_WORKERS=8
export COLLATZ_PREFER_GPU=true

# Worker settings
export COLLATZ_WORKER_NAME=production-node-01
export COLLATZ_LOG_LEVEL=INFO
```

### Batch Operations

**Create multiple accounts:**
```bash
#!/bin/bash
for name in alice bob charlie david; do
    python user_account.py create $name
done
```

**Start worker fleet:**
```bash
#!/bin/bash
for i in {1..10}; do
    python distributed_collatz.py \
        --user-key ./keys/fleet_account_private_key.pem \
        --worker-name "fleet-worker-$i" &
done
wait
```

### Integration with Monitoring Systems

**Prometheus metrics:**
```python
# Add to your monitoring stack
# Metrics available at http://localhost:8000/metrics
import prometheus_client

# Custom metrics
verification_counter = prometheus_client.Counter('collatz_verifications_total')
verification_timer = prometheus_client.Histogram('collatz_verification_duration_seconds')
```

**Log aggregation:**
```bash
# Centralized logging with structured JSON
export COLLATZ_LOG_FORMAT=json
export COLLATZ_LOG_FILE=/var/log/collatz/worker.log

# Integration with ELK stack, Splunk, etc.
```

---

## 🤝 Contributing to the Network

### Best Practices

**For Individual Users:**
- Keep your system updated and secure
- Monitor your worker's performance regularly
- Build trust by maintaining high uptime
- Report issues and bugs to help improve the network

**For Organizations:**
- Deploy multiple workers for redundancy
- Use dedicated accounts for organizational contributions
- Monitor fleet performance with centralized logging
- Consider contributing to development and documentation

**For Developers:**
- Study the codebase and architecture
- Submit pull requests for improvements
- Add support for new platforms and hardware
- Help with testing and quality assurance

### Scaling Your Contribution

**Single Machine:**
- Start with one worker to learn the system
- Add more workers as you gain experience
- Monitor resource usage to avoid overload
- Optimize for your specific hardware

**Multiple Machines:**
- Use consistent account across all machines
- Implement centralized monitoring and logging
- Stagger startup times to avoid network congestion
- Plan for maintenance and updates

**Cloud Deployment:**
- Use container orchestration (Kubernetes, Docker Swarm)
- Implement auto-scaling based on network demand
- Monitor costs and optimize instance types
- Consider spot instances for cost savings

### Network Citizenship

**Good Network Citizen:**
- ✅ Maintains consistent uptime
- ✅ Submits accurate results
- ✅ Responds to network needs (work generation, etc.)
- ✅ Helps other users with problems
- ✅ Reports bugs and issues

**What to Avoid:**
- ❌ Submitting false results (automatic detection will ban you)
- ❌ Overloading the network with too many workers
- ❌ Running on unstable systems that frequently crash
- ❌ Attempting to game the trust system

---

## 📈 Next Steps

### Immediate Actions
1. **[Get Started](#getting-started)**: Choose your participation method
2. **[Create Account](#user-accounts)**: Get credit for your contributions  
3. **[Monitor Progress](#understanding-your-progress)**: Track your statistics
4. **[Optimize Performance](#performance-optimization)**: Tune for your hardware

### Long-term Goals
1. **Build Trust**: Progress through trust levels consistently
2. **Scale Up**: Add more workers or upgrade hardware
3. **Contribute**: Help improve the project with feedback and code
4. **Stay Engaged**: Follow project updates and community discussions

### Community Involvement
- **GitHub**: Star the project, report issues, submit PRs
- **Leaderboard**: Compete friendly with other contributors
- **Documentation**: Help improve guides and tutorials
- **Testing**: Try new features and platforms

**Welcome to the Collatz Distributed Network community!** 🎉

*Together, we're tackling one of mathematics' greatest unsolved problems using the power of distributed computing and community collaboration.*