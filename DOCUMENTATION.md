# Documentation Index

Complete guide to Collatz Distributed Network documentation.

## Getting Started

📘 **[DISTRIBUTED_QUICKREF.md](DISTRIBUTED_QUICKREF.md)** - Start here!
- One-command installation
- Quick start guide
- User account setup
- Docker deployment
- Raspberry Pi setup

📗 **[README.md](README.md)** - Project overview
- Features and architecture
- Platform support
- How to contribute
- FAQ

🚀 **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment
- Installation methods for all platforms
- Docker and Kubernetes
- Raspberry Pi images
- Multi-node setup
- Cloud deployment

## Distributed Network

🌐 **[DISTRIBUTED.md](DISTRIBUTED.md)** - Complete distributed verification guide
- **Architecture:** Decentralized coordination via IPFS
- **Security Model:** Ed25519 signatures, Byzantine fault tolerance
- **Trust System:** Worker reputation and consensus requirements
- **Getting Started:** How to join as a worker node
- **Monitoring:** Network statistics and leaderboards
- **Advanced Usage:** Conflict resolution, cross-verification

**System Components:**
- 🔐 **[trust_system.py](trust_system.py)** - Worker reputation tracking
  - Trust levels (UNTRUSTED → VERIFIED → TRUSTED → ELITE)
  - Consensus calculation (3+ workers per range)
  - Automatic bad-actor detection and banning
  - Reputation scoring with decay for inactivity

- 📡 **[ipfs_coordinator.py](ipfs_coordinator.py)** - Work distribution
  - IPFS/IPNS state management (no deprecated pubsub!)
  - Work assignment with redundancy factor
  - Automatic timeout and reassignment
  - Global progress tracking

- ✍️ **[proof_verification.py](proof_verification.py)** - Cryptographic proofs
  - Ed25519 signature generation and verification
  - SHA-256 proof integrity checking
  - Cross-verification between workers
  - Conflict detection and resolution

- 🏭 **[distributed_collatz.py](distributed_collatz.py)** - Worker node
  - Integration with CollatzEngine
  - Keypair management
  - Work claiming and proof submission
  - Trust building over time

**Installation:**
```bash
# Install IPFS: https://docs.ipfs.tech/install/
ipfs init
ipfs daemon &

# Install Python dependencies
pip install -r requirements_distributed.txt

# Start worker node
python distributed_collatz.py
```

## Troubleshooting & Support

🔧 **[ERROR_HANDLING.md](ERROR_HANDLING.md)** - Complete troubleshooting guide
- Common issues and solutions
- Error log structure
- Diagnostic reports
- Recovery procedures
- Getting help

🩺 **Run Diagnostics:**
```bash
python run_diagnostics.py
```

## Contributing

🤝 **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
- Benchmark submissions (easy!)
- Code contributions (advanced)
- Guidelines and requirements
- What we're looking for

📊 **[benchmarks/README.md](benchmarks/README.md)** - Benchmark submission guide
- How to submit
- Naming conventions
- Privacy information
- What happens to data

## Community & Outreach

📢 **[REDDIT_POST.md](REDDIT_POST.md)** - Volunteer recruitment post
- Project description
- Hardware of interest
- Installation instructions
- Troubleshooting tips
- How to share results

## Technical Reference

### Main Scripts

- **`network_launcher.py`** - Distributed network launcher
  - Start coordinator or worker node
  - Manage IPFS connections
  - Monitor network statistics
  - Command-line: `python network_launcher.py`

- **`distributed_collatz.py`** - Worker node implementation
  - Connects to IPFS network
  - Receives work assignments
  - Submits verification results
  - Earns credits for contributions
  - Command-line: `python distributed_collatz.py`

- **`ipfs_coordinator.py`** - Network coordinator
  - Manages work distribution
  - Tracks worker contributions
  - Maintains global leaderboard
  - Handles result validation

- **`run_diagnostics.py`** - System health check
  - Hardware verification
  - Library checks
  - IPFS connectivity
  - Permission validation
  - Config file validation
  - Command-line: `python run_diagnostics.py`

### Support Modules

- **`error_handler.py`** - Error handling & logging
  - Centralized error logger
  - System diagnostics
  - Hardware checks
  - Config validation

- **`contribution_tracker.py`** - Contribution tracking
  - User profiles
  - Leaderboards
  - Export/merge functionality
  - Privacy-preserving hashing

### Configuration Files

All auto-generated and in `.gitignore`:

- **`collatz_config.json`** - Main engine state
  - Progress tracking
  - Highest proven number
  - Total tested count
  - Runtime statistics

- **`gpu_tuning.json`** - GPU optimization settings
  - Batch size
  - Threads per block
  - Work multiplier
  - Blocks per SM
  - CPU worker count

- **`autotuner_state.json`** - Auto-tuner resume state
  - Current stage
  - Best configuration
  - Best rate achieved
  - Iteration count
  - Timestamp

- **`optimization_state.json`** - Optimization status
  - Hardware fingerprint
  - Optimization completed flag
  - Benchmark completed flag
  - Last update timestamp

- **`error_log.json`** - Error history
  - Last 100 errors
  - Full stack traces
  - System information
  - Error categorization

- **`diagnostic_report.json`** - System health report
  - Library status
  - GPU availability
  - Permission checks
  - Config validation
  - Overall status

- **`user_profile.json`** - Contribution profile (optional)
  - Username
  - Machine ID (hashed)
  - Total contributions
  - Verification ranges

## Quick Reference

### First Run
```bash
python launcher.py
```
System optimizes automatically on first run (GPU mode).

### Subsequent Runs
```bash
python launcher.py
```
Skips optimization if hardware unchanged.

## File Structure

```
CollatzEngine/
├── README.md                    # Project overview
├── DEPLOYMENT.md               # Production deployment guide
├── DISTRIBUTED.md              # Network architecture details
├── DISTRIBUTED_QUICKREF.md     # Quick reference guide
├── ERROR_HANDLING.md           # Troubleshooting guide
├── CONTRIBUTING.md             # Contribution guidelines
├── USER_ACCOUNTS.md            # Account system documentation
├── REDDIT_POST.md              # Community post template
├── LICENSE                      # CC BY-NC-SA 4.0
│
├── network_launcher.py         # Network coordinator/worker
├── distributed_collatz.py      # Worker node implementation
├── ipfs_coordinator.py         # IPFS network coordination
├── run_diagnostics.py          # System check
│
├── user_account.py             # User accounts & credits
├── trust_system.py             # Peer trust management
├── proof_verification.py       # Result validation
├── contribution_tracker.py     # Contribution tracking
├── counterexample_handler.py   # Counterexample validation
├── error_handler.py            # Error handling
│
├── install.sh                  # Linux/Mac installer
├── install.ps1                 # Windows installer
├── Dockerfile                  # Container image
├── docker-compose.yml          # Multi-node setup
├── docker-entrypoint.sh        # Container entrypoint
├── build-pi-image.sh           # Raspberry Pi image builder
│
├── collatz_config.json         # (auto-generated)
├── error_log.json              # (auto-generated)
├── diagnostic_report.json      # (auto-generated)
│
└── benchmarks/
    ├── README.md               # Benchmark guide
    └── (community submissions)
```

## Getting Help

1. **Network setup:** [DISTRIBUTED_QUICKREF.md](DISTRIBUTED_QUICKREF.md)
2. **Deployment:** [DEPLOYMENT.md](DEPLOYMENT.md)
3. **Detailed troubleshooting:** [ERROR_HANDLING.md](ERROR_HANDLING.md)
4. **System diagnostics:** `python run_diagnostics.py`
5. **Error history:** Check `error_log.json`
6. **GitHub issues:** Include diagnostic report

## What to Read

**Just want to run it:**
→ [QUICK_START.md](QUICK_START.md)

**Want to understand how it works:**
→ [README.md](README.md)

**Having problems:**
→ [ERROR_HANDLING.md](ERROR_HANDLING.md)

**Want to contribute:**
→ [CONTRIBUTING.md](CONTRIBUTING.md)

**Want to share with others:**
→ [REDDIT_POST.md](REDDIT_POST.md)

---

**Most important:** Start with [QUICK_START.md](QUICK_START.md) if you're new! 🚀
