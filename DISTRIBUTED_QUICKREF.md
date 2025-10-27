# Distributed Collatz - Quick Reference

## 🚀 ONE-COMMAND INSTALL

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

### Raspberry Pi:
Download pre-built image: [Releases](https://github.com/Jaylouisw/ProjectCollatz/releases)

---

## 🎯 Quick Start (After Install)

**Just use the launcher menu:**

```bash
# Windows
cd %USERPROFILE%\collatz-network
.\start.ps1

# Linux/Mac
cd ~/collatz-network
./start.sh

# Or directly
python network_launcher.py
```

The launcher gives you a simple menu to:
- Create user accounts (option 4)
- Start worker nodes (options 1-3)
- View statistics and leaderboards (options 5-6)
- Manage the network (options 7-9)
- Run diagnostics (option 10)

**No need to remember commands!**

**Note:** Only one launcher instance can run per machine.

---

## 📦 Manual Installation (If You Prefer)

```bash
# 1. Install IPFS
# Download: https://docs.ipfs.tech/install/
ipfs init
ipfs daemon

# 2. Clone repository
git clone https://github.com/Jaylouisw/ProjectCollatz.git
cd ProjectCollatz

# 3. Install dependencies
pip install -r requirements_distributed.txt

# 4. Run the launcher
python network_launcher.py
```

---

## Manual Commands (If You Prefer)

```bash
# Create user account
python user_account.py create alice

# Start worker node with your account
python distributed_collatz.py --user-key ./keys/user_alice_private.pem

# Or run anonymous worker
python distributed_collatz.py
```

## 👤 User Accounts (NEW!)

### Create Account
```bash
# Creates Ed25519 keypair and registers user
python user_account.py create <username>
```

### Run Workers with Account
```bash
# Single worker
python distributed_collatz.py --user-key ./keys/user_alice_private.pem

# Multiple workers (same account)
python distributed_collatz.py --user-key ./keys/user_alice_private.pem --name alice-gpu1
python distributed_collatz.py --user-key ./keys/user_alice_private.pem --name alice-cpu2
```

### View Stats
```bash
# Your stats
python user_account.py stats <user_id>

# Leaderboard (top 10)
python user_account.py leaderboard

# Top 20
python user_account.py leaderboard --limit 20
```

### Benefits
- ✅ Track contributions across all your nodes
- ✅ Build reputation in the network
- ✅ Appear on leaderboards
- ✅ Persistent identity across sessions

**See [USER_ACCOUNTS.md](USER_ACCOUNTS.md) for full details!**

## 📊 Key Concepts

### Decentralized Architecture (NO Coordinator!)

- **Peer-to-Peer:** Any node with n>0 active peers self-organizes
- **Gossip Protocol:** Nodes sync state every 60s via IPFS
- **Auto Work Generation:** When frontier runs low, any node can create new work
- **Forever Network:** Runs indefinitely as long as n>0 nodes are active
- **No Single Point of Failure:** Any peer can publish state, merge from others

### Trust Levels
- **UNTRUSTED** (new) → 5 confirmations required
- **VERIFIED** (10+ correct) → 3 confirmations required  
- **TRUSTED** (100+ correct) → 2 confirmations required
- **ELITE** (1000+ correct, 0 errors) → 1 confirmation required
- **BANNED** (>10% error rate) → Permanently excluded

### User Accounts
- **Ed25519 Keypairs:** Cryptographic identity
- **Multiple Nodes:** Run many workers under one account
- **Contribution Tracking:** Aggregate stats across all your nodes
- **Leaderboards:** See top contributors network-wide
- **Persistent:** Identity survives across sessions/machines

### How It Works

1. **Discover Peers** - Find other nodes via IPFS swarm
2. **Sync State** - Gossip protocol merges network state (CRDT-style)
3. **Claim Work** - Get range assignment from shared work frontier
4. **Verify Range** - Run CollatzEngine on your GPU/CPU
5. **Sign Proof** - Generate Ed25519 signature of results
6. **Submit** - Upload proof to IPFS, update shared state
7. **Consensus** - Wait for N other workers to confirm (3+ by default)
8. **Update Contributions** - Your user account gets credit
9. **Trust Update** - Reputation increases if correct, decreases if wrong
10. **Generate More Work** - When frontier low, any node can extend it

### Security

- **Cryptographic Signatures:** Ed25519 prevents result tampering
- **Multi-Worker Verification:** 3+ workers must agree (Byzantine fault tolerance)
- **IPFS Immutability:** All proofs permanently stored, verifiable by anyone
- **Automatic Banning:** Workers with >10% error rate or 3 consecutive errors banned
- **Spot-Checking:** Even trusted workers randomly re-verified (2-10%)

## 🛠️ Worker Commands

```bash
# Start worker (GPU mode) - anonymous
python distributed_collatz.py

# Start worker with user account
python distributed_collatz.py --user-key ./keys/user_alice_private.pem

# CPU-only mode
python distributed_collatz.py --cpu-only --user-key ./keys/user_alice_private.pem

# Custom name
python distributed_collatz.py --name "MyGPU-RTX3050" --user-key ./keys/user_alice_private.pem

# Run 5 iterations (for testing)
python distributed_collatz.py --iterations 5

# Generate 100 new work assignments (any peer can do this!)
python distributed_collatz.py --generate-work 100
```

## 👤 Account Commands

```bash
# Create new user account
python user_account.py create <username>

# View your statistics
python user_account.py stats <user_id>

# View leaderboard
python user_account.py leaderboard

# Link existing worker to account (rarely needed - auto-linked when using --user-key)
python user_account.py link-node <user_id> <node_id>
```

## 📈 Monitoring

```python
# Check your trust level
from trust_system import TrustSystem
trust = TrustSystem()
stats = trust.get_worker_stats("QmYourNodeID")
print(f"Trust: {stats.trust_level.name}, Reputation: {stats.reputation_score:.1f}/100")

# View user aggregate stats (all your nodes combined)
from user_account import UserAccountManager
manager = UserAccountManager()
stats = manager.get_user_aggregate_stats("user_a1b2c3d4...")
print(f"Total Numbers: {stats['total_numbers_checked']:,}")
print(f"Total Ranges: {stats['total_ranges_completed']:,}")
print(f"Nodes: {stats['num_nodes']}")

# View network stats
from ipfs_coordinator import IPFSCoordinator
coord = IPFSCoordinator()
stats = coord.get_network_statistics()
print(f"Network Mode: {stats['network_mode']}")  # 'fully_decentralized'
print(f"Active workers: {stats['active_workers']}")
print(f"Known peers: {stats.get('known_peers', 0)}")
print(f"Highest proven: {stats['global_highest_proven']:,}")

# See trust leaderboard
top = trust.get_leaderboard(10)
for i, w in enumerate(top, 1):
    print(f"{i}. {w.worker_id[:16]}... - {w.trust_level.name}")

# See user contribution leaderboard
from user_account import UserAccountManager
manager = UserAccountManager()
leaders = manager.get_leaderboard(limit=10)
for i, user in enumerate(leaders, 1):
    print(f"{i}. {user['username']} - {user['total_numbers_checked']:,} numbers")
```

## ⚠️ Important Files

- **`./keys/user_*_private.pem`** - YOUR USER ACCOUNT! Backup this file securely!
- **`worker_keypair_*.json`** - Worker node identity (auto-generated per node)
- **`trust_database.json`** - Network trust/reputation data
- **`user_accounts.json`** - User account database
- **`collatz_config.json`** - Your local verification progress

## � Docker Deployment

### Single Container:
```bash
# Pull image
docker pull jaylouisw/collatz-network:latest

# Run worker node
docker run -d --name collatz-worker \
  -v collatz-ipfs:/home/collatz/.ipfs \
  -v collatz-keys:/app/keys \
  jaylouisw/collatz-network

# Run with user account (mount your keys)
docker run -d --name collatz-worker \
  -v $PWD/keys:/app/keys:ro \
  -v collatz-ipfs:/home/collatz/.ipfs \
  jaylouisw/collatz-network \
  python distributed_collatz.py --user-key /app/keys/user_alice_private.pem
```

### Multi-Node Testing (docker-compose):
```bash
# Start 3-node network for testing
docker-compose up -d

# View logs
docker-compose logs -f worker1

# Stop network
docker-compose down
```

### Build Your Own Image:
```bash
docker build -t collatz-network .
docker run -it collatz-network
```

## 🥧 Raspberry Pi

### Pre-built Image:
1. Download from [Releases](https://github.com/Jaylouisw/ProjectCollatz/releases)
2. Write to SD card: `etcher` or `dd`
3. Boot Pi - auto-starts on first boot!

### Manual Install on Pi:
```bash
# Use the install script
curl -sSL https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.sh | bash

# Or build custom image
./build-pi-image.sh
```

**Pi Features:**
- Headless (no GUI) - perfect for clusters
- Auto-starts on boot
- SSH enabled by default
- Tested on: Pi 3, Pi 4, Pi Zero 2 W

## 🖥️ Platform Support

**Tested & Supported:**
- ✅ Windows 10/11 (x64)
- ✅ Ubuntu 20.04/22.04/24.04 (x64, ARM64)
- ✅ Debian 11/12 (x64, ARM64)
- ✅ macOS 11+ (Intel & Apple Silicon)
- ✅ Raspberry Pi OS (ARM64)
- ✅ Docker (all platforms)

**Requirements:**
- Python 3.8 or later
- 2GB RAM minimum (4GB+ recommended)
- Internet connection
- IPFS daemon

## �🔗 Full Documentation

- **[DISTRIBUTED.md](DISTRIBUTED.md)** - Complete distributed system architecture
- **[USER_ACCOUNTS.md](USER_ACCOUNTS.md)** - User account system guide
- **[ERROR_HANDLING.md](ERROR_HANDLING.md)** - Error handling and recovery
- **[README.md](README.md)** - Project overview

