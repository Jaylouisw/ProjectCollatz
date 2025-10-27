# Collatz Distributed Network v1.0.1

**Join the global effort to solve the Collatz Conjecture!**

A fully decentralized verification network powered by IPFS, with cryptographic proofs, Byzantine fault tolerance, and permanent public records. **Now with complete future-proofing** - works on any OS and hardware configuration with graceful degradation and protocol independence. Contribute computing power from anywhere and help explore one of mathematics' greatest unsolved problems.

📚 **Get Started:** [DISTRIBUTED_QUICKREF.md](DISTRIBUTED_QUICKREF.md) | **Full Documentation:** [DISTRIBUTED.md](DISTRIBUTED.md) | **Deployment:** [DEPLOYMENT.md](DEPLOYMENT.md)

## 🚀 One-Command Install

### Windows (PowerShell):
```powershell
iwr -useb https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.ps1 | iex
```

### Linux / macOS:
```bash
curl -sSL https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.sh | bash
```

### Docker:
```bash
docker pull jaylouisw/collatz-network:latest
docker run -it jaylouisw/collatz-network
```

### Raspberry Pi & SBCs:
Download pre-built images from [Releases](https://github.com/Jaylouisw/ProjectCollatz/releases)

**→ See [DISTRIBUTED_QUICKREF.md](DISTRIBUTED_QUICKREF.md) for complete installation guide!**

## 📱 Pre-Built SBC Images ![SBC Images](https://img.shields.io/badge/SBC%20Images-automated-brightgreen)

**Ready-to-use images** for Single Board Computers with Collatz Network pre-installed:

- **🍓 Raspberry Pi** (all models with both 32-bit and 64-bit OS options where supported)
- **🟠 Orange Pi** (64-bit and 32-bit ARM variants) 
- **🪨 Rock Pi** (ARM64 and ARM32 models)
- **⚡ Odroid** (ARM-based variants)
- **🔧 Any ARM SBC** with Ubuntu support

**🔄 Auto-Updated:** New images are automatically built on every release using GitHub Actions.

**📋 Quick Setup:**
1. **Download** appropriate image from [latest release](https://github.com/Jaylouisw/ProjectCollatz/releases/latest)
2. **Flash** to SD card using [Etcher](https://www.balena.io/etcher/) 
3. **Boot** and wait for auto-setup (5-10 minutes)
4. **SSH** in and run: `cd ~/collatz-network && python3 network_launcher.py`
5. **Join** the network: Create account → Start worker → Contribute computing power!

---

## Features

**🌐 Fully Decentralized Network**
- No central server - runs forever via IPFS peer-to-peer gossip
- Network continues with n>0 active nodes
- Self-organizing work generation
- Permanent public verification records

**🔐 Cryptographic Security**
- Ed25519 signatures prevent tampering
- 3+ worker consensus required
- Random work assignment prevents collusion
- Trust & reputation system with automatic bad-actor detection
- Anti-self-verification prevents single-node attacks

**🔮 Future-Proof Architecture (NEW in v1.0.1)**
- **Protocol Independence**: IPFS now, libp2p ready, any future protocol
- **Hardware Abstraction**: CPU always works, GPU optional, future accelerators ready
- **Cross-Platform**: Windows/Linux/macOS with automatic compatibility detection
- **Dependency Flexibility**: Version ranges prevent breakage from updates
- **Graceful Degradation**: System works even with missing optional components

**🎉 Community Features**
- User accounts with persistent identity
- Global leaderboard on IPFS
- Counterexample celebration with network voting
- Credit system for contributors
- Raspberry Pi and Docker support

**⚡ High Performance**
- Multi-backend compute engine (CPU/CUDA/ROCm auto-selection)
- Multi-node horizontal scaling
- Automatic hardware optimization
- ~10 billion numbers/sec per GPU node

**→ See [DISTRIBUTED.md](DISTRIBUTED.md) for complete architecture details!**

---

## Quick Start

### 1. Install (Choose One Method)

**Windows:**
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
docker run -it jaylouisw/collatz-network
```

**Raspberry Pi:**
Download pre-built image from [Releases](https://github.com/Jaylouisw/ProjectCollatz/releases)

### 2. Create User Account

```bash
python network_launcher.py
# Choose option 4: Create User Account
```

Your account gives you:
- ✅ Persistent identity across all your nodes
- ✅ Recognition on the global leaderboard
- ✅ Credit if you find a counterexample!

### 3. Start Contributing

```bash
python network_launcher.py
# Choose option 1: Start Worker Node (with account)
```

Your node will:
- Connect to the global IPFS network
- Get randomly assigned verification work
- Build trust/reputation over time
- Contribute to mathematical history!

**That's it!** Your node is now part of the distributed verification network.

### 4. Future-Proof Engine (NEW in v1.0.1)

Try the new future-proofed engine with cross-platform compatibility:

```bash
# Check system compatibility
python future_proof_engine.py --info

# Run functionality test
python future_proof_engine.py --test

# Start in local mode (works offline)
python future_proof_engine.py --local

# Full distributed mode with auto-detection
python future_proof_engine.py
```

The future-proof engine automatically:
- ✅ Detects your hardware (CPU/GPU) and uses the best available
- ✅ Selects optimal network transport (IPFS/local/future protocols)
- ✅ Handles missing dependencies gracefully
- ✅ Works across all platforms and architectures

---

## Platform Support

**✅ Future-Proofed Compatibility Matrix:**

| Platform | Architecture | Python | Network | Compute | Status |
|----------|-------------|---------|---------|---------|---------|
| **Windows** | x64 | 3.8+ | ✅ IPFS | ✅ CPU/CUDA | **VERIFIED** |
| **Windows** | ARM64 | 3.8+ | ✅ IPFS | ✅ CPU/GPU | **SUPPORTED** |
| **Linux** | x64 | 3.8+ | ✅ IPFS | ✅ CPU/CUDA/ROCm | **SUPPORTED** |
| **Linux** | ARM64 | 3.8+ | ✅ IPFS | ✅ CPU/GPU | **SUPPORTED** |
| **macOS** | Intel | 3.8+ | ✅ IPFS | ✅ CPU/Metal | **SUPPORTED** |
| **macOS** | Apple Silicon | 3.8+ | ✅ IPFS | ✅ CPU/Metal | **SUPPORTED** |
| **Docker** | Any | 3.8+ | ✅ IPFS | ✅ Auto-detect | **SUPPORTED** |
| **Raspberry Pi** | ARM64/32 | 3.8+ | ✅ IPFS | ✅ CPU | **SUPPORTED** |

**🔧 Hardware Support:**
- **CPU-Only**: Always works (universal fallback)
- **NVIDIA GPU**: CUDA acceleration when available
- **AMD GPU**: ROCm acceleration (ready)
- **Intel GPU**: OpenCL support (ready)
- **Apple Silicon**: Metal compute (ready)
- **Future Hardware**: Extensible plugin architecture

**📦 Requirements:**
- Python 3.8+ (flexible version ranges)
- 2GB RAM minimum (4GB+ recommended) 
- Network transport (IPFS primary, fallbacks available)
- Internet connection (optional for local testing)

**🚀 Performance Modes:**
- **Local Mode**: Works offline for testing
- **Network Mode**: Full distributed operation
- **Hybrid Mode**: Network + local verification

---

## Documentation

**📚 User Guides:**
- **[DISTRIBUTED_QUICKREF.md](DISTRIBUTED_QUICKREF.md)** - Quick reference guide
- **[DISTRIBUTED.md](DISTRIBUTED.md)** - Complete network architecture
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[USER_ACCOUNTS.md](USER_ACCOUNTS.md)** - User account system
- **[ERROR_HANDLING.md](ERROR_HANDLING.md)** - Troubleshooting

**🔒 Security & Future-Proofing (NEW):**
- **[COMPREHENSIVE_SECURITY_ANALYSIS.md](COMPREHENSIVE_SECURITY_ANALYSIS.md)** - Complete security documentation
- **[FUTURE_PROOFING_COMPLETE.md](FUTURE_PROOFING_COMPLETE.md)** - Future-proofing implementation guide
- **[FUTURE_PROOFING_ANALYSIS.md](FUTURE_PROOFING_ANALYSIS.md)** - Technical analysis of future-proofing measures

---

## Advanced Topics

### Manual Installation

If you prefer not to use the install scripts:

```bash
# Install IPFS
# Download from: https://docs.ipfs.tech/install/

# Clone repository
git clone https://github.com/Jaylouisw/ProjectCollatz.git
cd ProjectCollatz

# Install Python dependencies
pip install -r requirements_distributed.txt

# Start IPFS daemon
ipfs init
ipfs daemon &

# Run the launcher
python network_launcher.py
```

### Multi-Node Setup

Run multiple worker nodes under one account:

```bash
# Terminal 1
python distributed_collatz.py --user-key ./keys/user_alice_private.pem --name node1

# Terminal 2  
python distributed_collatz.py --user-key ./keys/user_alice_private.pem --name node2

# Terminal 3
python distributed_collatz.py --user-key ./keys/user_alice_private.pem --name node3
```

All nodes contribute to your total statistics!

### GPU Acceleration

For 10x-100x speedup, install GPU support:

```bash
# CUDA 12.x
pip install cupy-cuda12x

# CUDA 11.x
pip install cupy-cuda11x
```

Then start workers normally - GPU will be auto-detected and used.

### Docker Deployment

```bash
# Single node
docker run -d --name collatz-worker \
  -v collatz-ipfs:/home/collatz/.ipfs \
  -v $PWD/keys:/app/keys:ro \
  jaylouisw/collatz-network \
  python distributed_collatz.py --user-key /app/keys/user_alice_private.pem

# Multi-node network
docker-compose up -d
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete Docker guide.

---

## How It Works

### The Collatz Conjecture

Take any positive integer:
- If even: divide by 2
- If odd: multiply by 3 and add 1
- Repeat until you reach 1

**The conjecture:** Every number eventually reaches 1.

**Status:** Unproven! Verified up to 2^68 by previous efforts.

**Our goal:** Extend verification further AND create permanent, trustworthy records.

### The Distributed Network

1. **Work Generation:** Network automatically generates verification tasks
2. **Random Assignment:** Workers randomly selected to prevent collusion
3. **Verification:** Each range verified by 3+ independent workers
4. **Consensus:** Results must agree (Byzantine fault tolerance)
5. **Publication:** Cryptographically signed results stored permanently on IPFS
6. **Trust Building:** Workers build reputation through consistent correct results

If a counterexample is found:
1. 🎉 Network-wide celebration with full credit to finder
2. 🗳️ Democratic vote on whether to continue
3. 📜 Permanent record of the discovery on IPFS

### Why IPFS?

- **Decentralized:** No single point of failure
- **Permanent:** Content-addressed storage lasts forever
- **Tamper-proof:** Cryptographic hashing prevents alterations
- **Global:** Anyone can verify results independently

---

## Contributing

Ways to contribute:

1. **Run a worker node** - Add computing power to the network
2. **Run multiple nodes** - Scale horizontally for more impact
3. **Report issues** - Help improve the system
4. **Share the project** - Grow the network
5. **Code contributions** - Submit PRs for improvements

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Performance Benchmarks

**Per-Node Performance:**
- CPU-only: ~100-500 million numbers/sec (varies by CPU)
- Single GPU: ~10 billion numbers/sec (mid-range GPU)
- Multi-GPU: Scales linearly

**Network Performance:**
- 10 nodes: ~100+ billion numbers/sec
- 100 nodes: ~1+ trillion numbers/sec
- Scales indefinitely with more participants!

**Current Progress:**
- Check network statistics: `python network_launcher.py` → option 9
- View leaderboard: `python user_account.py leaderboard`

---

## FAQ

**Q: Do I need a powerful computer?**
A: No! CPU-only mode works fine. Any contribution helps.

**Q: How much internet bandwidth does this use?**
A: Very little. IPFS gossip is efficient, typically <1 MB/hour.

**Q: Can I run this on a Raspberry Pi?**
A: Yes! We provide pre-built Pi images. Perfect for 24/7 operation.

**Q: What if I find a counterexample?**
A: 🎉 You'll be credited! The network celebrates and votes on continuation.

**Q: Is this safe to run?**
A: Yes. Open source, no data collection, no crypto mining. Just math!

**Q: How do I know my contribution matters?**
A: Check your statistics and the leaderboard. Every number counts!

**Q: Can I stop and restart anytime?**
A: Yes! Your progress and reputation persist across sessions.

---

## License

This project is licensed under CC BY-NC-SA 4.0 (Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International).

**You are free to:**
- Share and adapt the work
- Run the distributed network
- Modify for personal/educational use

**Under these terms:**
- Attribution required
- Non-commercial use only
- Share-alike (derivatives under same license)

See [LICENSE](LICENSE) for full details.

---

## Support

- **Documentation:** [DISTRIBUTED.md](DISTRIBUTED.md)
- **Quick Start:** [DISTRIBUTED_QUICKREF.md](DISTRIBUTED_QUICKREF.md)
- **Deployment:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **Issues:** https://github.com/Jaylouisw/ProjectCollatz/issues
- **Diagnostics:** `python run_diagnostics.py`

---

**Ready to contribute?** Install now and join the global verification network! 🚀

## Platform Support

**Tested & Working:**
- ✅ Windows 10/11 (x64)
- ✅ Ubuntu 20.04/22.04/24.04 (x64, ARM64)
- ✅ Debian 11/12 (x64, ARM64)
- ✅ macOS 11+ (Intel & Apple Silicon)
- ✅ Raspberry Pi OS (ARM64)
- ✅ Docker (all platforms)

**Requirements:**
- Python 3.8+
- 2GB RAM minimum (4GB+ recommended)
- For distributed network: IPFS daemon
- For GPU mode: CUDA-capable GPU

## Contributing

Want to help verify the Collatz Conjecture? Join the distributed network above, or contribute code improvements via pull requests.

## License

Copyright (c) 2025 Jay (CollatzEngine)

This work is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-nc-sa/4.0/).

[![CC BY-NC-SA 4.0](https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png)](http://creativecommons.org/licenses/by-nc-sa/4.0/)

**You are free to:**
- **Share** — copy and redistribute the material in any medium or format
- **Adapt** — remix, transform, and build upon the material

**Under the following terms:**
- **Attribution** — You must give appropriate credit to Jay (CollatzEngine), provide a link to the license, and indicate if changes were made.
- **NonCommercial** — You may not use the material for commercial purposes.
- **ShareAlike** — If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.

See the [LICENSE](LICENSE) file for full details.

## Acknowledgments

Built with CuPy for CUDA acceleration. Thanks to all GPU benchmark volunteers!
