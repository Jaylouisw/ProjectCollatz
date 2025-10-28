# ProjectCollatz - Distributed Verification Network

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](https://github.com/Jaylouisw/ProjectCollatz)
[![Status](https://img.shields.io/badge/status-alpha-yellow)](https://github.com/Jaylouisw/ProjectCollatz)

**ALPHA SOFTWARE - EDUCATIONAL/RESEARCH USE ONLY**

This is an educational project exploring distributed systems through AI-assisted development. While core functionality works, this is **not production-ready** and has not undergone independent security audit. See the [wiki](../../wiki) for complete documentation.

A distributed verification system exploring the Collatz Conjecture using IPFS peer-to-peer coordination. The project implements GPU-accelerated verification with cryptographic result signing.

**[📚 Wiki](../../wiki)** | **[Quick Start](../../wiki/Quick-Start)** | **[Installation](../../wiki/Installation)** | **[Security](../../wiki/Security)**

---

## Quick Start

### One-Command Install

**Linux / macOS:**
```bash
curl -sSL https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/quick-install.sh | bash
```

**Windows (PowerShell):**
```powershell
iwr -useb https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.ps1 | iex
```

**Docker:**
```bash
docker-compose up -d
```

### Start Contributing

```bash
python network_launcher.py
# Choose: Create Account → Start Worker
```

Your node joins the IPFS network and begins verification.

---

## Project Status

### Currently Implemented

**Core Functionality:**
- CPU Verification - Multi-threaded Collatz verification engine
- GPU Acceleration - CUDA support for NVIDIA GPUs (10-100x speedup)
- IPFS Coordination - Decentralized work distribution via IPFS
- User Accounts - Persistent identity with Ed25519 key pairs
- Progress Tracking - Range assignment and completion tracking
- Multi-Node Support - Multiple workers per user account
- Auto-Updates - Git-based updates for Docker and systemd

**Security Features:**
- Ed25519 Signatures - Cryptographic signing of verification results
- Content Addressing - IPFS hash-based integrity
- Public Verification - All results published to IPFS
- Worker Identity - Unique peer IDs for tracking

See [SECURITY.md](SECURITY.md) for complete security assessment.

### In Development

- Multi-Verifier Consensus - Framework exists, needs wider testing
- Trust/Reputation System - Basic scoring implemented, Byzantine tolerance in progress
- Anti-Self-Verification - Design complete, enforcement testing

### Planned

- Independent Security Audit - Seeking security researchers
- Byzantine Fault Tolerance - Full BFT consensus for untrusted networks
- Web Interface - Browser-based worker participation
- AMD GPU Support - ROCm acceleration
- Mobile Apps - iOS/Android clients

See [VERSIONING.md](VERSIONING.md) for protocol evolution roadmap.

### Known Limitations

- **No Independent Audit**: Project has not undergone professional security review
- **Alpha Software**: Expect bugs, breaking changes, incomplete features
- **Small Network**: Limited nodes reduce Byzantine fault tolerance
- **Trust Model**: Relies on honest majority assumption

**Status:** Research/educational project exploring distributed verification. Treat results as experimental.

---

## Current Capabilities

### Network
- Decentralized coordination via IPFS (no central server)
- Automatic work distribution with self-assignment
- Real-time progress tracking across all nodes
- Fault recovery with automatic task reassignment

### Performance
- CPU Mode: 100-500 million numbers/second (varies by CPU)
- GPU Mode: ~10 billion numbers/second (mid-range NVIDIA GPU)
- Multi-Node: Linear scaling with additional workers

### Deployment
- One-command installers for all platforms
- Docker support with `docker-compose up -d`
- Git-based auto-updates from GitHub
- Pre-built images for Raspberry Pi/SBC

---

## Installation

### Supported Platforms

| Platform | Architecture | Python | Network | Compute | Status |
|----------|-------------|---------|---------|---------|---------|
| Windows | x64 | 3.8+ | IPFS | CPU/CUDA | Tested |
| Linux | x64 | 3.8+ | IPFS | CPU/CUDA | Tested |
| Linux | ARM64 | 3.8+ | IPFS | CPU | Tested |
| macOS | Intel/M1/M2 | 3.8+ | IPFS | CPU | Tested |
| Docker | Multi-arch | 3.8+ | IPFS | Auto-detect | Tested |
| Raspberry Pi | ARM64/32 | 3.8+ | IPFS | CPU | Tested |

### Requirements

- Python 3.8 or higher
- 2GB RAM minimum (4GB+ recommended)
- <100MB storage for software
- Internet connection for IPFS coordination
- Optional: CUDA-capable GPU for acceleration

### Quick Install Scripts

Install scripts handle all dependencies automatically:

**Linux/macOS:**
```bash
curl -sSL https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/quick-install.sh | bash
```

Script performs:
- Python 3.8+ verification
- Virtual environment creation
- Python dependency installation
- IPFS v0.31.0 download and installation
- IPFS repository initialization
- IPFS daemon startup

**Windows (PowerShell as Administrator):**
```powershell
iwr -useb https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.ps1 | iex
```

### Docker Installation

Recommended for servers and continuous operation:

```bash
# Clone repository
git clone https://github.com/Jaylouisw/ProjectCollatz.git
cd ProjectCollatz

# Start with auto-updates enabled
docker-compose up -d
```

Docker deployment includes:
- Automatic daily updates from GitHub
- Health checks
- Restart on failure
- Persistent IPFS data and keys

### Manual Installation

```bash
# Install IPFS from https://docs.ipfs.tech/install/

# Clone repository
git clone https://github.com/Jaylouisw/ProjectCollatz.git
cd ProjectCollatz

# Install dependencies
pip install -r requirements_distributed.txt

# Initialize and start IPFS
ipfs init
ipfs daemon &

# Run launcher
python network_launcher.py
```

### Raspberry Pi / SBC

Pre-built images available at [Releases](https://github.com/Jaylouisw/ProjectCollatz/releases)

Supported hardware:
- Raspberry Pi (all models)
- Orange Pi series
- Rock Pi series
- Odroid series
- Any ARM64/ARM32 with Ubuntu

---

## Usage

### Interactive Mode (Recommended)

```bash
python network_launcher.py
```

Menu:
1. Create User Account - Generate identity keypair
2. Start Worker - Join network and begin computing
3. View Statistics - See contribution metrics
4. View Leaderboard - Check global rankings

### Direct Worker Mode

For automation or multi-node setups:

```bash
# Run with user key
python distributed_collatz.py --user-key ./keys/username_private_key.pem

# Multiple nodes under one account
python distributed_collatz.py --user-key ./keys/alice.pem --name node1
python distributed_collatz.py --user-key ./keys/alice.pem --name node2
python distributed_collatz.py --user-key ./keys/alice.pem --name node3
```

### GPU Acceleration

For 10x-100x speedup, install CUDA:

```bash
# CUDA 12.x
pip install cupy-cuda12x

# CUDA 11.x
pip install cupy-cuda11x
```

GPU will be auto-detected on startup.

---

## How It Works

### The Collatz Conjecture

Algorithm:
- If n is even: n → n/2
- If n is odd: n → 3n+1
- Repeat until reaching 1

**Conjecture:** This process always reaches 1 for any positive integer.

**Status:** Unproven. Verified computationally up to 2^68.

**Goal:** Extend verification with cryptographically-signed records.

### Distributed Network

Architecture:
1. **Work Generation** - Network automatically creates verification tasks
2. **Random Assignment** - Workers randomly selected to prevent collusion
3. **Verification** - Independent verification by assigned workers
4. **Consensus** - Framework for multi-worker agreement (in development)
5. **Publication** - Cryptographically signed results stored on IPFS
6. **Trust Building** - Reputation system tracks worker consistency

### IPFS Implementation

Benefits:
- **Decentralized** - No single point of failure
- **Permanent** - Content-addressed storage
- **Tamper-proof** - Cryptographic hashing
- **Global** - Independent verification capability

---

## Documentation

### Core Documentation
- [SECURITY.md](SECURITY.md) - Security assessment and vulnerabilities
- [VERSIONING.md](VERSIONING.md) - Protocol evolution strategy
- [INSTALLATION.md](INSTALLATION.md) - Detailed installation guide
- [USER_GUIDE.md](USER_GUIDE.md) - Complete user documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture

### Additional Resources
- [GitHub Wiki](https://github.com/Jaylouisw/ProjectCollatz/wiki) - Comprehensive docs
- [Quick Start](https://github.com/Jaylouisw/ProjectCollatz/wiki/Quick-Start) - Getting started
- [Troubleshooting](https://github.com/Jaylouisw/ProjectCollatz/wiki/Troubleshooting) - Common issues
- [FAQ](https://github.com/Jaylouisw/ProjectCollatz/wiki/FAQ) - Frequently asked questions

---

## Contributing

Contribution methods:
1. **Run Worker Nodes** - Add compute power
2. **Scale Operations** - Run multiple nodes
3. **Report Issues** - Improve the system
4. **Share Project** - Grow the network
5. **Code Contributions** - Submit pull requests
6. **Security Review** - Audit the codebase

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Security

**Security Status:** This project implements basic cryptographic primitives (Ed25519 signatures, SHA-256 hashing) but has not undergone independent security audit. Trust model assumes honest majority. Suitable for research/educational use.

**Implemented:**
- Ed25519 digital signatures on verification results
- IPFS content-addressed storage
- Worker identity tracking
- Public verification records

**In Development:**
- Multi-verifier consensus (3+ independent confirmations)
- Byzantine fault tolerance
- Anti-self-verification enforcement
- Reputation-based trust system

**Known Vulnerabilities:**
- Sybil attacks (single entity, multiple identities)
- Eclipse attacks (network partition)
- Trust score manipulation
- Consensus bypass

See [SECURITY.md](SECURITY.md) for complete details and disclosure process.

**Security researchers:** We welcome your review. Contact: jay@projectcollatz.com

---

## Performance

**Per-Node:**
- CPU-only: 100-500 million numbers/second (varies by processor)
- Single GPU: ~10 billion numbers/second (mid-range GPU)
- Multi-GPU: Linear scaling

**Network:**
- 10 nodes: 100+ billion numbers/second
- 100 nodes: 1+ trillion numbers/second
- Scales linearly with participants

**Resource Usage:**
- Memory: 2GB minimum, 4GB+ recommended
- Disk: <100MB
- Network: <1 MB/hour typical
- Power: CPU-efficient algorithms

---

## FAQ

**Q: Do I need a powerful computer?**  
A: No. CPU-only mode works. Any contribution helps.

**Q: Internet bandwidth requirements?**  
A: Minimal. IPFS gossip typically <1 MB/hour.

**Q: Raspberry Pi support?**  
A: Yes. Pre-built images available. Suitable for 24/7 operation.

**Q: What if I find a counterexample?**  
A: Credited discovery. Network records the finding.

**Q: Is this safe to run?**  
A: Yes. Open source, no data collection, no cryptocurrency mining.

**Q: How is contribution tracked?**  
A: Statistics and leaderboard show verification progress.

**Q: Can I stop and restart?**  
A: Yes. Progress and reputation persist across sessions.

**Q: Cryptocurrency involvement?**  
A: None. Pure mathematical verification. No blockchain.

---

## License

Licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/):

- Share - Copy and redistribute
- Adapt - Remix and build upon
- Attribution - Credit required
- NonCommercial - Not for commercial use
- ShareAlike - Distribute under same license

Copyright (c) 2025 Jay Wenden (CollatzEngine)

See [LICENSE](LICENSE) for details.

---

## About

The Collatz Conjecture (3n+1 problem) is an unsolved problem in mathematics. This project provides a distributed, cryptographically-signed approach to extend computational verification while creating transparent records of mathematical progress.

---

## Documentation

Complete documentation available in the **[Project Wiki](../../wiki)**:

- **[Quick Start Guide](../../wiki/Quick-Start)** - Get running in 5 minutes
- **[Installation Guide](../../wiki/Installation)** - Detailed setup for all platforms
- **[User Guide](../../wiki/User-Guide)** - How to participate
- **[Architecture](../../wiki/Architecture)** - Technical design
- **[Security](../../wiki/Security)** - Trust and verification
- **[Development Roadmap](../../wiki/Development-Roadmap)** - Future plans
- **[Troubleshooting](../../wiki/Troubleshooting)** - Common issues
- **[FAQ](../../wiki/FAQ)** - Frequently asked questions

---

## Support

- **Documentation**: [Project Wiki](../../wiki)
- **Issues**: [GitHub Issues](https://github.com/Jaylouisw/ProjectCollatz/issues)
- **Diagnostics**: `python run_diagnostics.py`
- **Community**: [Discussions](https://github.com/Jaylouisw/ProjectCollatz/discussions)
