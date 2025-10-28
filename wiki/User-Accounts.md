# User Account System

## Overview

The distributed Collatz network supports **user accounts** that allow you to:
- Track contributions across multiple worker nodes
- Build reputation in the network
- View leaderboards showing top contributors
- Maintain identity across sessions

Each user account is secured with an **Ed25519 cryptographic keypair**. Your private key stays on your machine and proves you own your contributions.

## Quick Start

### 1. Create a User Account

```bash
python user_account.py create <username>
```

Example:
```bash
python user_account.py create alice
```

**Output:**
```
✅ User account created!
User ID: user_a1b2c3d4...
Username: alice
Private Key: ./keys/user_alice_private.pem
Public Key: ./keys/user_alice_public.pem

🔐 KEEP YOUR PRIVATE KEY SAFE!
Anyone with this key can claim your contributions.
```

**Important:** Back up your private key file! If you lose it, you'll lose access to your account.

### 2. Run Workers with Your Account

Use your private key to run worker nodes that contribute under your username:

```bash
python distributed_collatz.py --user-key ./keys/user_alice_private.pem
```

You can run **multiple workers** with the same key across different machines - all contributions count toward your total!

### 3. View Your Stats

```bash
python user_account.py stats <user_id>
```

Or check the leaderboard:

```bash
python user_account.py leaderboard
```

## How It Works

### User Account Structure

Each user account has:
- **User ID**: SHA-256 hash of your public key (permanent identifier)
- **Username**: Human-readable name you choose
- **Private Key**: Proves you own the account (keep secret!)
- **Public Key**: Shared with network (verifies your signatures)

### Contribution Tracking

When your worker completes a verification range:
1. Worker creates cryptographically signed proof
2. Network verifies proof reached consensus (3+ workers agree)
3. Your user account records:
   - Numbers checked
   - Ranges completed
   - Compute time
4. Contributions persist across all your nodes

### Multiple Nodes Per User

You can run as many worker nodes as you want under one account:

```bash
# Machine 1 (GPU)
python distributed_collatz.py --user-key ./keys/user_alice_private.pem

# Machine 2 (CPU)
python distributed_collatz.py --user-key ./keys/user_alice_private.pem --cpu-only

# Machine 3 (second GPU)
python distributed_collatz.py --user-key ./keys/user_alice_private.pem --name alice-gpu2
```

All three nodes contribute to the same user account!

## CLI Reference

### Create Account
```bash
python user_account.py create <username>
```
Creates new Ed25519 keypair and registers user.

**Options:**
- `<username>`: Your chosen username (letters, numbers, underscores only)

**Output:**
- User ID
- Private key location
- Public key location

### View Stats
```bash
python user_account.py stats <user_id>
```
Shows detailed statistics for a user account.

**Output:**
- Username
- Total numbers checked
- Total ranges completed
- Total compute time
- Number of worker nodes
- Trust level (based on consensus history)

### View Leaderboard
```bash
python user_account.py leaderboard [--limit N]
```
Shows top contributors sorted by total contributions.

**Options:**
- `--limit N`: Show top N users (default: 10)

**Output:**
- Rank
- Username
- Total numbers checked
- Total ranges completed
- Total compute time

### Link Existing Worker
```bash
python user_account.py link-node <user_id> <node_id>
```
Manually link an existing worker node to your account.

**Note:** Workers automatically link when started with `--user-key`, so you rarely need this.

## Worker Integration

### Run Worker with Account

```bash
python distributed_collatz.py --user-key ./keys/user_alice_private.pem
```

The worker will:
1. Load your user account from private key
2. Register itself as a node under your account
3. Show your username in output
4. Track all contributions to your account
5. Display updated stats after each verification

**Example Output:**
```
[WORKER] 👤 Loaded user account: alice (user_a1b2c3d4...)
[WORKER] 🔨 Starting verification of range:
[WORKER]   User: alice
[WORKER]   Range: 1,000,000 to 2,000,000
[WORKER]   Numbers: ~1,000,000
[WORKER] ✅ Verification complete in 42.5s
[WORKER] 👤 User Stats: 5,000,000 numbers | 5 ranges | 210.3s total
```

### Anonymous Workers

Workers can run without user accounts:

```bash
python distributed_collatz.py
```

Anonymous workers still contribute to the network, but:
- No persistent identity across sessions
- No leaderboard ranking
- No cross-node contribution aggregation
- Stats tracked per-node only

## Security

### Private Key Protection

Your private key is **everything**. Anyone with access can:
- Impersonate you
- Claim your contributions
- Damage your reputation

**Best Practices:**
1. ✅ Store private keys in secure location (encrypted drive)
2. ✅ Use file permissions: `chmod 600 keys/*.pem` (Linux/Mac)
3. ✅ Back up keys to separate secure location
4. ❌ Never commit keys to git
5. ❌ Never share keys via email/chat
6. ❌ Never store keys in cloud sync folders

### Cryptographic Verification

The network uses **Ed25519 signatures** to verify:
- You own your user account
- Work proofs came from your nodes
- No one can forge your contributions

When you submit work:
1. Worker signs proof with your private key
2. Network verifies signature with your public key
3. Only valid signatures are accepted
4. Signature proves ownership without revealing private key

### Trust System Integration

User accounts interact with the trust system:
- New users start at **UNTRUSTED** level
- Successful verifications increase trust
- Consensus failures decrease trust
- Reputation persists across nodes
- High trust users need fewer confirmations

**Trust Levels:**
- **UNTRUSTED**: Requires 5+ worker consensus
- **VERIFIED**: Requires 3+ worker consensus (default)
- **TRUSTED**: Requires 2+ worker consensus
- **ELITE**: Single-worker verification accepted
- **BANNED**: All submissions rejected

## Network Statistics

### View Network-Wide Stats

The distributed coordinator tracks:
- Total users registered
- Total worker nodes active
- Top contributors by numbers checked
- Network progress (highest verified range)

Access via coordinator API:
```python
from ipfs_coordinator import IPFSCoordinator

coordinator = IPFSCoordinator()
stats = coordinator.get_network_statistics()
print(f"Total Users: {stats.get('total_users', 0)}")
print(f"Active Nodes: {stats.get('active_workers', 0)}")
```

### Aggregate Stats Across Your Nodes

If you run multiple nodes, view combined statistics:

```python
from user_account import UserAccountManager

manager = UserAccountManager()
stats = manager.get_user_aggregate_stats(user_id)
print(f"Total across {stats['num_nodes']} nodes:")
print(f"  Numbers: {stats['total_numbers_checked']:,}")
print(f"  Ranges: {stats['total_ranges_completed']:,}")
print(f"  Time: {stats['total_compute_time']:.1f}s")
```

## Troubleshooting

### "Failed to load user account"

**Cause:** Private key file not found or invalid format.

**Solutions:**
1. Check file path is correct
2. Verify key file exists: `ls ./keys/`
3. Ensure key wasn't corrupted (restore from backup)

### "User ID mismatch"

**Cause:** Private key doesn't match expected public key.

**Solutions:**
1. Verify you're using correct key file
2. Check for multiple keys with similar names
3. Recreate account if key was lost

### "Contributions not updating"

**Cause:** Verification didn't reach consensus or worker not linked.

**Solutions:**
1. Check worker logs for consensus messages
2. Verify worker started with `--user-key` parameter
3. Ensure trust system is working (3+ workers verifying ranges)
4. Check account manager is initialized (should see "Loaded user account" message)

### "Multiple nodes showing same stats"

**Expected behavior!** All nodes under one user show the **same aggregate stats** - this is by design. Each node contributes to your total account statistics.

## Advanced Usage

### Migrate Worker to New Account

To move a worker from anonymous to user account:

```bash
# Stop anonymous worker (Ctrl+C)

# Restart with user key
python distributed_collatz.py --user-key ./keys/user_alice_private.pem
```

Worker will automatically link to your account on next run.

### Change Username

Currently usernames are permanent after creation. To change:
1. Create new account with desired username
2. Run workers with new private key
3. Old account stats remain separate

(Future versions may support username changes)

### Export/Import Account

**Export:**
```bash
# Private key contains everything needed
cp ./keys/user_alice_private.pem /secure/backup/location/
```

**Import on new machine:**
```bash
# Copy key to new machine
cp /secure/backup/location/user_alice_private.pem ./keys/

# Run worker with existing key
python distributed_collatz.py --user-key ./keys/user_alice_private.pem
```

The network automatically recognizes existing accounts - no registration needed!

## See Also

- **DISTRIBUTED.md** - Full distributed system architecture
- **DISTRIBUTED_QUICKREF.md** - Quick command reference
- **trust_system.py** - Trust/reputation implementation
- **ipfs_coordinator.py** - Network coordination (peer-to-peer)
- **proof_verification.py** - Cryptographic signature system
