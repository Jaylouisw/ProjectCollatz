# Versioning & Future-Proofing Strategy

## Semantic Versioning

ProjectCollatz follows [Semantic Versioning 2.0.0](https://semver.org/):

**MAJOR.MINOR.PATCH** (e.g., `1.2.3`)

- **MAJOR**: Incompatible protocol or API changes
- **MINOR**: Backward-compatible new features
- **PATCH**: Backward-compatible bug fixes

### Pre-1.0 Versioning
During alpha/beta development (versions 0.x.x):
- **0.MINOR.PATCH** indicates unstable APIs
- Breaking changes can occur in MINOR versions
- Protocol may change without backward compatibility
- **Current version**: `0.1.0-alpha`

### Version Milestones

| Version | Status | Description |
|---------|--------|-------------|
| 0.1.x-alpha | Current | Core functionality, local testing |
| 0.2.x-alpha | Planned | Full IPFS distribution, basic security |
| 0.3.x-beta | Planned | Byzantine fault tolerance, verification redundancy |
| 0.9.x-rc | Planned | Security audit complete, production-ready features |
| 1.0.0 | Goal | Stable protocol, backward compatibility guaranteed |

## Protocol Versioning

### Network Protocol Version
Each network message includes a protocol version header:

```python
{
    "protocol_version": "0.1",
    "message_type": "work_assignment",
    "data": { ... }
}
```

### Backward Compatibility Strategy

#### For MAJOR Version Changes (e.g., 0.1 → 1.0 → 2.0)
- **Breaking changes** require coordinated network upgrade
- Deprecation warnings issued 2 minor versions in advance
- Dual-protocol support during transition period (3-6 months)
- Clear migration guide published

**Example**:
```
Version 1.8.0: Announce protocol 2.0 coming, publish migration guide
Version 1.9.0: Enable dual-mode (support both 1.x and 2.0 protocols)
Version 2.0.0: Protocol 2.0 becomes primary, 1.x deprecated
Version 2.1.0: Drop 1.x support
```

#### For MINOR Version Changes (e.g., 1.0 → 1.1 → 1.2)
- **Additive changes only** (new optional fields, new message types)
- Old clients ignore unknown fields/messages
- New clients handle missing optional fields gracefully

#### For PATCH Version Changes (e.g., 1.0.0 → 1.0.1)
- **No protocol changes** - only bug fixes
- Fully transparent to network

## Cryptographic Agility

To ensure long-term security against future cryptographic attacks (e.g., quantum computers):

### Current Cryptography
| Component | Algorithm | Key Size | Security Level |
|-----------|-----------|----------|----------------|
| Hashing | SHA-256 | N/A | 128-bit |
| Signatures | Ed25519 | 256-bit | 128-bit |
| IPFS | SHA-256 (multihash) | N/A | 128-bit |

### Algorithm Versioning
All cryptographic operations include an algorithm identifier:

```python
{
    "signature_algorithm": "ed25519",
    "signature": "...",
    "hash_algorithm": "sha256",
    "hash": "..."
}
```

### Planned Cryptographic Transitions

#### Phase 1: Algorithm Identifier Support (v0.2.0)
- ✅ Add algorithm version fields to all signed/hashed data
- Goal: Enable future algorithm changes without protocol breakage

#### Phase 2: Hybrid Cryptography (v0.5.0)
- Add support for multiple signature algorithms simultaneously
- Begin dual-signing critical messages (Ed25519 + post-quantum candidate)

#### Phase 3: Post-Quantum Transition (v1.5.0+)
- **Trigger**: NIST post-quantum standards finalized
- Introduce post-quantum signature algorithm (e.g., Dilithium, SPHINCS+)
- Dual-mode: Accept both Ed25519 and PQ signatures
- Timeline: 2-3 years for full migration

#### Phase 4: Deprecate Legacy (v2.0.0+)
- Remove Ed25519-only support
- All signatures must use post-quantum algorithm

### Hash Function Agility
If SHA-256 is compromised:
- Introduce new hash function via MINOR version update
- Use multihash format (IPFS CIDv1) to support multiple hash functions
- Nodes can verify old content with old hash, new content with new hash

## Upgrade Mechanisms

### Automatic Updates
**Goal**: Minimize user intervention while maintaining security

#### Docker Deployments
```yaml
# docker-compose.yml
services:
  projectcollatz:
    image: ghcr.io/jaylouisw/projectcollatz:latest
    restart: unless-stopped
    environment:
      - AUTO_UPDATE=true  # Pull latest image on restart
```

#### Native Installations
```bash
# Systemd service with auto-update
[Service]
ExecStartPre=/opt/projectcollatz/update.sh
ExecStart=/opt/projectcollatz/run.sh
Restart=always
```

Auto-update script checks GitHub releases and pulls changes before start.

#### Raspberry Pi / SBC Images
- Image includes systemd timer for daily update checks
- Updates staged and applied on next reboot
- Rollback to previous version if boot fails

### Manual Upgrade Process
For users who prefer manual control:

```bash
# Check current version
python distributed_collatz.py --version

# Pull latest code
git fetch origin
git checkout v0.2.0  # or latest release tag

# Apply migrations (if needed)
python migrate.py --from 0.1.0 --to 0.2.0

# Restart services
systemctl restart projectcollatz
```

### Breaking Change Notifications
When a breaking upgrade is required:
1. **In-app notification**: Warning banner in CLI output
2. **IPFS network message**: Broadcast deprecation notice
3. **GitHub release notes**: Detailed migration guide
4. **Grace period**: Minimum 30 days before old protocol stops working

## Data Migration Strategy

### State Format Versioning
All persistent data includes a format version:

```json
{
    "format_version": "0.1",
    "data": {
        "coordinator_state": { ... },
        "verified_ranges": [ ... ]
    }
}
```

### Migration Scripts
Each MAJOR/MINOR version update includes migration tooling:

```python
# Example: migrate.py
def migrate_0_1_to_0_2(old_state):
    """Migrate state from v0.1 to v0.2 format."""
    new_state = {
        "format_version": "0.2",
        "data": {
            "coordinator_state": old_state["data"]["coordinator_state"],
            "verified_ranges": old_state["data"]["verified_ranges"],
            # NEW: Add reputation tracking
            "worker_reputation": {}
        }
    }
    return new_state
```

### Backup & Rollback
Before applying migrations:
```bash
# Automatic backup
cp state.json state.json.backup-$(date +%Y%m%d)

# If migration fails, rollback
mv state.json.backup-YYYYMMDD state.json
git checkout v0.1.0
```

## API Stability Guarantees

### Core APIs (v1.0+)
Once v1.0.0 is released, these interfaces are **stable**:
- `IPFSCoordinator` class constructor
- `register_worker()` method signature
- `claim_assignment()` method signature
- `submit_proof()` method signature
- Network protocol message formats

**Breaking changes** to stable APIs require MAJOR version bump.

### Experimental APIs
Marked with `@experimental` decorator:
```python
@experimental(version="0.2.0")
def advanced_verification_strategy(...):
    """May change without notice in pre-1.0 versions."""
    pass
```

## Configuration Compatibility

### Configuration File Versioning
```json
{
    "config_version": "0.1",
    "network": { ... },
    "gpu_settings": { ... }
}
```

### Forward Compatibility
- New releases can read old config files (with warnings about deprecated fields)
- Unknown fields in config are ignored (logged as warnings)

### Backward Compatibility
- **Not guaranteed pre-1.0**: Older releases may not read newer config files
- Post-1.0: Configs are backward compatible within same MAJOR version

## Deprecation Policy

### Deprecation Process
1. **Announce**: Add deprecation warning in code/docs (VERSION N)
2. **Grace Period**: Feature continues to work (VERSION N+1, N+2)
3. **Remove**: Feature removed (VERSION N+3 or next MAJOR)

**Minimum grace period**: 6 months or 2 MINOR versions (whichever is longer)

### Example Deprecation Timeline
```
Version 0.2.0: Deprecate legacy work assignment format
               Warning: "Legacy format deprecated, will be removed in 0.4.0"

Version 0.3.0: Continue supporting both formats with warnings

Version 0.4.0: Remove legacy format support
               (or delay to v1.0.0 if timeline too short)
```

## Testing & Validation

### Pre-Release Validation
Before each release:
- [ ] Unit tests (100% pass rate required)
- [ ] Integration tests (multi-node scenarios)
- [ ] Backward compatibility tests (old clients with new coordinator)
- [ ] Forward compatibility tests (new clients with old coordinator)
- [ ] Migration script dry-run
- [ ] Security regression tests

### Canary Deployments
For MAJOR/MINOR updates:
1. Deploy to test network (public testnet)
2. Monitor for 2 weeks
3. Deploy to 10% of production nodes
4. Monitor for 1 week
5. Full rollout

## Documentation Standards

Each release includes:
- **CHANGELOG.md**: Human-readable list of changes
- **MIGRATION_GUIDE.md**: Step-by-step upgrade instructions
- **API_CHANGELOG.md**: Detailed API changes (for developers)
- **BREAKING_CHANGES.md**: All incompatibilities (if any)

## Community Communication

Release announcements posted to:
- GitHub Releases
- Project website
- Reddit r/Collatz
- Discord server (future)
- IPFS pubsub topic: `/projectcollatz/announcements`

## Long-Term Support (LTS) Releases

**Post-1.0 plan**: Every 4th MINOR version is designated LTS

| Version | Type | Support Window |
|---------|------|----------------|
| 1.4.x | LTS | 2 years |
| 1.8.x | LTS | 2 years |
| 2.4.x | LTS | 2 years |

LTS versions receive:
- Security patches
- Critical bug fixes
- No new features
- Extended community support

## Conclusion

ProjectCollatz is designed for long-term evolution:
- **Clear versioning** ensures users understand compatibility
- **Cryptographic agility** prepares for future security challenges
- **Graceful upgrades** minimize disruption to the network
- **Transparent communication** keeps community informed

As the project matures, these policies will be refined based on real-world experience and community feedback.

---

**Last Updated**: 2025-10-28
**Document Version**: 1.0
**Current Project Version**: 0.1.0-alpha
