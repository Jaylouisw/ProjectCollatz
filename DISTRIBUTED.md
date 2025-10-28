# Distributed Collatz Verification Network

## 🌐 Overview

The Distributed Collatz project transforms the CollatzEngine into a **trustless, decentralized verification network** using IPFS, cryptographic proofs, and Byzantine fault-tolerant consensus.

**Key Features:**
- ✅ **Decentralized coordination** via IPFS (no central server)
- ✅ **Cryptographic signatures** (Ed25519) prevent result tampering
- ✅ **Multi-worker verification** (3+ workers verify each range)
- ✅ **Trust/reputation system** with automatic bad-actor detection
- ✅ **Conflict resolution** via independent re-verification
- ✅ **Public, immutable proofs** stored on IPFS forever

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                 IPFS Network Layer                        │
│  ┌──────────────┐    ┌──────────────┐                    │
│  │ Work         │    │ Verification │                    │
│  │ Assignments  │◄──►│ Proofs       │                    │
│  │ (docstore)   │    │ (eventlog)   │                    │
│  └──────────────┘    └──────────────┘                    │
│          ▲                   ▲                             │
│          │  IPNS Publishing  │                            │
│          └───────────────────┘                            │
└──────────────────────────────────────────────────────────┘
                       ▲
                       │ Read/Write
                       ▼
┌──────────────────────────────────────────────────────────┐
│            Distributed Worker Nodes                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Worker 1     │  │ Worker 2     │  │ Worker N     │   │
│  │ (GPU/CPU)    │  │ (GPU/CPU)    │  │ (GPU/CPU)    │   │
│  │ Trust: Elite │  │ Trust: New   │  │ Trust: Banned│   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│         │                  │                  ✗           │
│         ▼                  ▼                               │
│  ┌─────────────────────────────────────┐                 │
│  │   Trust & Verification System       │                 │
│  │  - Consensus checking (3+ workers)  │                 │
│  │  - Cryptographic signatures         │                 │
│  │  - Reputation scoring                │                 │
│  │  - Conflict detection                │                 │
│  └─────────────────────────────────────┘                 │
└──────────────────────────────────────────────────────────┘
```

---

## 🔐 Security Model

### Trust Levels

| Level | Criteria | Confirmations Required | Spot-Check Rate |
|-------|----------|------------------------|-----------------|
| **UNTRUSTED** | New worker, no history | 5 workers | 100% (always verified) |
| **VERIFIED** | 10+ correct verifications | 3 workers | 10% random spot-checks |
| **TRUSTED** | 100+ correct verifications | 2 workers | 5% random spot-checks |
| **ELITE** | 1000+ correct, 0 errors | 1 worker (+ spot-checks) | 2% random spot-checks |
| **BANNED** | >10% error rate or 3 consecutive errors | ∞ (ignored) | N/A |

### Verification Workflow

```
1. Worker claims range assignment
   └─> IPFS Coordinator assigns work
   
2. Worker verifies range locally (GPU/CPU)
   └─> Uses CollatzEngine to check convergence
   
3. Worker generates cryptographic proof
   ├─> SHA-256 hash of results
   ├─> Ed25519 signature with private key
   └─> Upload detailed proof to IPFS
   
4. Submit signed proof to network
   └─> IPFS Coordinator receives proof
   
5. Trust system validates proof
   ├─> Verify cryptographic signature
   ├─> Check proof integrity (hash match)
   ├─> Cross-check with other workers
   └─> Reach consensus (N out of M must agree)
   
6. Update trust/reputation
   ├─> Correct workers: +reputation, +trust level
   ├─> Incorrect workers: -reputation, possible ban
   └─> Consensus reached: range marked complete
   
7. Publish results via IPNS
   └─> Global state updated, accessible to all nodes
```

### Byzantine Fault Tolerance

**Problem:** Malicious workers could submit false results.

**Solution:** Multi-layer defense:

1. **Redundant Verification:** Each range verified by 3+ independent workers
2. **Consensus Requirements:** All verifications must agree
3. **Cryptographic Signatures:** Workers can't tamper with results after submission
4. **Trust Scoring:** Bad actors lose reputation and get banned automatically
5. **Spot-Checking:** Even trusted workers randomly re-verified
6. **Conflict Resolution:** Disagreements trigger independent verification

**Attack Scenarios:**

| Attack | Defense |
|--------|---------|
| Submit false results | ❌ Requires 3+ colluding workers (statistically unlikely) |
| Tamper with past proofs | ❌ IPFS content-addressing makes proofs immutable |
| Forge other worker's signature | ❌ Ed25519 public-key cryptography |
| Sybil attack (many fake workers) | ❌ All new workers start UNTRUSTED, need 10+ correct verifications |
| Claim work but never complete | ❌ Automatic timeout and reassignment after 1 hour |

---

## 📦 Components

### 1. `trust_system.py`

**Purpose:** Manages worker reputation and consensus tracking.

**Key Classes:**
- `TrustLevel`: Enum for worker trust levels
- `WorkerStats`: Per-worker statistics and reputation
- `VerificationResult`: Result from a worker's verification
- `ConsensusState`: Tracks consensus for a specific range
- `TrustSystem`: Main trust management logic

**Key Methods:**
```python
# Register a new worker
trust.register_worker(worker_id) -> WorkerStats

# Submit verification for consensus
trust.submit_verification(result) -> (consensus_reached, message)

# Resolve conflicts after independent check
trust.resolve_conflict(range_start, range_end, correct_result, 
                      correct_workers, incorrect_workers)

# Get trust statistics
trust.get_statistics() -> Dict
trust.get_leaderboard(top_n) -> List[WorkerStats]
```

### 2. `ipfs_coordinator.py`

**Purpose:** Coordinates work distribution via IPFS.

**Key Classes:**
- `WorkAssignment`: A range assignment for verification
- `VerificationProof`: A proof submitted by a worker
- `IPFSCoordinator`: Main coordination logic

**Key Methods:**
```python
# Claim available work
coordinator.claim_work(worker_id) -> WorkAssignment

# Submit verification proof
coordinator.submit_verification_proof(...) -> proof_id

# Generate new work at frontier
coordinator.generate_work_frontier(start_from, num_assignments)

# Publish state to IPNS
coordinator.save_state_to_ipns()

# Get network statistics
coordinator.get_network_statistics() -> Dict
```

### 3. `proof_verification.py`

**Purpose:** Cryptographic proof generation and verification.

**Key Classes:**
- `SignedProof`: A cryptographically signed verification proof
- `ProofVerificationSystem`: Verification and signature checking

**Key Methods:**
```python
# Generate worker keypair
verifier.generate_worker_keypair() -> (private_key, public_key)

# Create signed proof
verifier.create_signed_proof(private_key, ...) -> SignedProof

# Validate proof authenticity
verifier.validate_proof(signed_proof) -> (valid, error_message)

# Submit for consensus checking
verifier.submit_for_consensus(signed_proof) -> (consensus, message)

# Detect conflicting results
verifier.detect_conflicts(range_start, range_end) -> List[SignedProof]
```

### 4. `distributed_collatz.py`

**Purpose:** Worker node that joins the distributed network.

**Key Class:**
- `DistributedCollatzWorker`: Main worker implementation

**Key Methods:**
```python
# Claim and verify work
worker.claim_and_verify_work() -> bool

# Run continuous worker loop
worker.run_worker_loop(num_iterations=None)

# Show statistics
worker.show_statistics()
```

---

## 🚀 Getting Started

### Prerequisites

```bash
# Install IPFS
# Download from: https://docs.ipfs.tech/install/
# Or via package manager:
# Windows: choco install ipfs
# Linux: snap install ipfs
# Mac: brew install ipfs

# Initialize IPFS
ipfs init

# Start IPFS daemon
ipfs daemon

# Install Python dependencies
pip install ipfshttpclient cryptography
```

### Running a Worker Node

```bash
# Basic usage (GPU mode)
python distributed_collatz.py

# CPU-only mode
python distributed_collatz.py --cpu-only

# Custom worker name
python distributed_collatz.py --name "MyGPUWorker"

# Connect to custom IPFS API
python distributed_collatz.py --ipfs-api /ip4/192.168.1.100/tcp/5001

# Run limited iterations (for testing)
python distributed_collatz.py --iterations 5

# Generate new work assignments (coordinator role)
python distributed_collatz.py --generate-work 100
```

### First-Time Setup

```bash
# 1. Start IPFS daemon
ipfs daemon &

# 2. Generate initial work assignments (run once)
python distributed_collatz.py --generate-work 100

# 3. Start your worker
python distributed_collatz.py --name "MyWorker-GPU-RTX3050"

# Worker will:
# - Generate cryptographic keypair (saved to worker_keypair_*.json)
# - Load network state from IPNS
# - Claim work assignment
# - Verify range
# - Submit signed proof
# - Build reputation over time
```

**⚠️ IMPORTANT:** Backup your `worker_keypair_*.json` file! It's your worker identity and reputation.

---

## 📊 Monitoring

### View Your Worker Stats

```python
from trust_system import TrustSystem

trust = TrustSystem()
stats = trust.get_worker_stats("QmYourWorkerID")

print(f"Trust Level: {stats.trust_level.name}")
print(f"Reputation: {stats.reputation_score}/100")
print(f"Correct: {stats.correct_verifications}")
print(f"Incorrect: {stats.incorrect_verifications}")
```

### View Network Stats

```python
from ipfs_coordinator import IPFSCoordinator

coordinator = IPFSCoordinator()
stats = coordinator.get_network_statistics()

print(f"Active workers: {stats['active_workers']}")
print(f"Total assignments: {stats['total_assignments']}")
print(f"Completed: {stats['completed_assignments']}")
print(f"Global highest proven: {stats['global_highest_proven']:,}")
```

### View Leaderboard

```python
from trust_system import TrustSystem

trust = TrustSystem()
top_workers = trust.get_leaderboard(top_n=10)

for i, worker in enumerate(top_workers, 1):
    print(f"{i}. {worker.worker_id[:16]}... - {worker.trust_level.name} - "
          f"Rep: {worker.reputation_score:.1f}")
```

---

## 🔬 Advanced Usage

### Running a Coordinator Node

A coordinator generates work assignments for the network:

```python
from ipfs_coordinator import IPFSCoordinator

coordinator = IPFSCoordinator()

# Generate work frontier (e.g., at 10^18)
start_from = 1000000000000000000
assignments = coordinator.generate_work_frontier(
    start_from=start_from,
    num_assignments=1000  # Create 1000 work chunks
)

print(f"Generated {len(assignments)} assignments")
print(f"Range: {assignments[0].range_start:,} to {assignments[-1].range_end:,}")
```

### Cross-Verifying Other Workers

Want to verify someone else's work (build trust faster)?

```python
from ipfs_coordinator import IPFSCoordinator

coordinator = IPFSCoordinator()

# Get assignments that need more verifications
for assignment in coordinator.work_assignments.values():
    if (assignment.status in ['available', 'in_progress'] and
        len(assignment.assigned_workers) < assignment.redundancy_factor):
        
        print(f"Assignment needs verification:")
        print(f"  Range: {assignment.range_start:,} to {assignment.range_end:,}")
        print(f"  Progress: {len(assignment.assigned_workers)}/{assignment.redundancy_factor}")
```

### Resolving Conflicts

If workers disagree, independent verification is needed:

```python
from proof_verification import ProofVerificationSystem
from trust_system import TrustSystem

trust = TrustSystem()
verifier = ProofVerificationSystem(trust)

# Check for conflicts
conflicting_proofs = verifier.detect_conflicts(range_start, range_end)

if conflicting_proofs:
    print(f"⚠️ Conflict detected!")
    for proof in conflicting_proofs:
        print(f"  Worker {proof.worker_id[:16]}... says: {proof.all_converged}")
    
    # Re-verify independently
    correct_result = verify_range_independently(range_start, range_end)
    
    # Identify correct/incorrect workers
    correct = [p.worker_id for p in conflicting_proofs if p.all_converged == correct_result]
    incorrect = [p.worker_id for p in conflicting_proofs if p.all_converged != correct_result]
    
    # Resolve conflict (updates trust)
    verifier.resolve_conflict_with_independent_verification(
        range_start, range_end, correct_result
    )
```

---

## 🎯 Contribution Guidelines

### How to Help

1. **Run a worker node** - Contribute your GPU/CPU to the verification effort
2. **Report bugs** - Help improve the distributed system
3. **Improve algorithms** - Optimize verification performance
4. **Documentation** - Help explain complex concepts

### Worker Reputation

Your worker's reputation is determined by:
- ✅ **Accuracy** - Correct verifications increase reputation
- ✅ **Volume** - More verifications = higher trust level
- ✅ **Consistency** - No errors for long periods
- ❌ **Errors** - Incorrect results decrease reputation
- ❌ **Inactivity** - Reputation decays if inactive for 30+ days

**Goal:** Reach **ELITE** status (1000+ correct verifications, 0 errors)

---

## 🛡️ Security Considerations

### Threats and Mitigations

| Threat | Mitigation |
|--------|------------|
| **Result tampering** | Ed25519 signatures + IPFS content-addressing |
| **Sybil attacks** | New workers start UNTRUSTED, must prove themselves |
| **Collusion** | Need 3+ workers to collude (statistically unlikely at scale) |
| **Lazy workers** | Automatic timeout and reassignment after 1 hour |
| **Key theft** | Workers should backup and secure keypair files |
| **IPFS node compromise** | All proofs are public, verifiable by anyone |

### Best Practices

1. **Backup your keypair** - Store `worker_keypair_*.json` securely
2. **Run your own IPFS node** - Don't trust public gateways
3. **Verify others** - Cross-check other workers' results to build trust
4. **Monitor reputation** - Check your trust level regularly
5. **Report conflicts** - If you detect disagreements, report them

---

## 📈 Performance Optimization

### Maximizing Verification Rate

```python
# Use GPU for maximum speed
python distributed_collatz.py  # GPU mode (10B+ odd/sec)

# CPU mode is slower but still contributes
python distributed_collatz.py --cpu-only  # CPU mode (1-2M odd/sec)

# Run multiple workers on multi-GPU systems
python distributed_collatz.py --name "Worker-GPU-0" &
python distributed_collatz.py --name "Worker-GPU-1" &
```

### Reducing IPNS Update Overhead

The coordinator publishes to IPNS every 5 minutes by default. Adjust if needed:

```python
coordinator = IPFSCoordinator()
coordinator.STATE_PUBLISH_INTERVAL = 600  # 10 minutes instead of 5
```

---

## 🐛 Troubleshooting

### IPFS Connection Issues

```bash
# Check if IPFS daemon is running
ipfs swarm peers

# If no peers, check firewall
# IPFS uses ports: 4001 (swarm), 5001 (API), 8080 (gateway)

# Restart daemon
pkill ipfs
ipfs daemon
```

### Worker Banned Unexpectedly

Check logs for verification errors:

```python
from trust_system import TrustSystem

trust = TrustSystem()
stats = trust.get_worker_stats("QmYourWorkerID")

print(f"Correct: {stats.correct_verifications}")
print(f"Incorrect: {stats.incorrect_verifications}")
print(f"Error rate: {stats.incorrect_verifications / stats.total_verifications:.1%}")
```

If error rate > 10%, you'll be banned. Possible causes:
- GPU instability (thermal throttling, overclocking)
- Software bugs
- Hardware errors

### No Work Available

```python
# Generate new work assignments
python distributed_collatz.py --generate-work 100
```

---

## 🔗 References

- **IPFS:** https://ipfs.tech
- **Ed25519:** https://ed25519.cr.yp.to/
- **Collatz Conjecture:** https://en.wikipedia.org/wiki/Collatz_conjecture
- **Byzantine Fault Tolerance:** https://en.wikipedia.org/wiki/Byzantine_fault

---

## 📄 License

Copyright (c) 2025 Jay Wenden (CollatzEngine)  
Licensed under CC BY-NC-SA 4.0

https://creativecommons.org/licenses/by-nc-sa/4.0/

---

**Ready to contribute? Start your worker node and help verify the Collatz conjecture!** 🚀
