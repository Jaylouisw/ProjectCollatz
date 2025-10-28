# GitHub Copilot Instructions for ProjectCollatz

## Project Overview

**ProjectCollatz** is an educational distributed computing project exploring the Collatz Conjecture through IPFS-based peer-to-peer verification. This is an **AI-collaborative development project** where AI agents (Claude, GitHub Copilot) generate the majority of code, while the human maintainer provides architecture, design decisions, and responds to community feedback.

**Current Status**: Alpha (v0.1.0-alpha) - Research/educational project, not production-ready.

**Primary Goal**: Learn distributed systems architecture through iterative AI-assisted development and community feedback.

## Core Development Principles

### 1. Honesty Over Marketing

**NEVER**:
- Make claims about "entirely new architecture" or "revolutionary" approaches
- Promise "complete Byzantine fault tolerance" without actual implementation
- Use marketing language like "perfect for" or "the future of"
- Overstate security without independent audit
- Claim features are "production-ready" when they're experimental

**ALWAYS**:
- Clearly mark alpha/beta status
- Separate "Implemented" vs "Partially Implemented" vs "Planned"
- Document known vulnerabilities and limitations
- Use technical descriptions instead of buzzwords
- State when features need testing or are framework-only

### 2. No Placeholder Code in Core Functionality

**Reddit Criticism Addressed**: Community (u/gandalfpc) caught placeholder verification code that returned `True` after `time.sleep(1)`. This destroyed credibility.

**Rule**: Core verification, consensus, and security code must have REAL implementations, not placeholders.

**Acceptable placeholders**:
- Future features marked as `LibP2PTransport` (documented as "infrastructure ready")
- AMD GPU support (waiting for CuPy-ROCm stability)
- Network coordination stubs in future-proof abstraction layers

**Unacceptable placeholders**:
- Verification functions (CPU/GPU)
- Consensus mechanisms
- Security/cryptographic operations
- User authentication
- Data integrity checks

**When adding TODO comments**:
```python
# Acceptable:
# TODO: Add AMD ROCm support when CuPy-ROCm becomes stable

# Unacceptable:
# TODO: Implement actual verification (placeholder)
return True  # Placeholder
```

### 3. Document Implementation Status Clearly

In all documentation files (README, SECURITY, VERSIONING, etc.):

**Use status indicators**:
- "Currently Implemented" - Actually working, tested code
- "In Development" / "Partially Implemented" - Framework exists, needs testing
- "Planned" - Design documented, code not started

**In SECURITY.md**, use visual indicators:
- ✅ Implemented
- 🚧 Partially Implemented
- ❌ Planned/Not Implemented

**In code comments**:
```python
# IMPLEMENTED: Ed25519 signature verification
# PARTIAL: Multi-verifier consensus (framework exists, needs wider testing)
# PLANNED: Post-quantum cryptography
```

### 4. Technical Accuracy

**Cryptography**:
- Only claim "Ed25519 signatures" if actually using `cryptography.hazmat.primitives.asymmetric.ed25519`
- Only claim "SHA-256 hashing" if using `hashlib.sha256`
- Never say "military-grade encryption" - say "AES-256" or "Ed25519"

**Distributed Systems**:
- "IPFS-based coordination" not "blockchain"
- "Honest majority trust model" not "completely trustless"
- "Peer-to-peer" not "decentralized autonomous"
- "Content-addressed storage" not "immutable blockchain"

**Byzantine Fault Tolerance**:
- Only claim BFT if implementing actual consensus algorithm (PBFT, Raft, etc.)
- "BFT-aware architecture" or "BFT framework" for partial implementations
- Document the f/(3f+1) threshold if claiming Byzantine tolerance

### 5. Emoji Usage Policy

**Documentation (.md files)**:
- Minimize emoji use in technical documentation
- Status indicators (✅ 🚧 ❌) are acceptable for clarity
- Remove emoji from claims like "🚀 Revolutionary!" or "✨ Amazing!"
- Technical descriptions should be emoji-free

**Code output (console)**:
- Emoji acceptable for user-facing output (helps scanning)
- Examples: `[IPFS] 🌐 Node initialized` or `✓ Test passed`
- Keep functional messages emoji-free: `[ERROR] Connection failed`

**Git commits**:
- No emoji in commit messages
- Use conventional commit format: `fix: resolve peer discovery error`

## Architecture Guidelines

### Core Components

1. **CollatzEngine.py** - Verification engine (GPU/CPU)
   - Real CUDA kernels via CuPy
   - Multiprocessing CPU fallback
   - Returns dict format: `{'counterexample': None|int, 'numbers_checked': int}`

2. **distributed_collatz.py** - Worker node implementation
   - Must call actual `gpu_check_range()` and `cpu_check_range()` from CollatzEngine.py
   - No placeholder verification functions
   - Proper error handling and fallbacks

3. **ipfs_coordinator.py** - IPFS-based coordination
   - Work assignment and distribution
   - Peer discovery (with graceful failure handling)
   - Trust system integration
   - State publishing to IPFS

4. **user_account.py** - User identity management
   - Ed25519 keypair generation
   - Account persistence
   - Username uniqueness enforcement
   - Multi-node support per account

5. **trust_system.py** - Reputation and anti-gaming
   - Track worker reliability
   - Anti-self-verification (creator can't verify own work)
   - Byzantine-aware scoring (framework, needs testing)

6. **network_transport.py** - Protocol abstraction layer
   - IPFSTransport (implemented)
   - LibP2PTransport (infrastructure only)
   - LocalTransport (fallback)

7. **compute_engine.py** - Hardware abstraction
   - CUDAEngine (implemented)
   - CPUEngine (implemented)
   - ROCmEngine (placeholder for AMD)

### Future-Proofing Architecture

The project has abstraction layers for network protocols and compute engines to enable future protocol changes without breaking existing code:

**Network Transport Abstraction**:
- Abstract base class `NetworkTransport`
- Current: IPFS via `ipfshttpclient`
- Future: libp2p, WebRTC, custom protocols
- Design allows swapping protocols without rewriting worker code

**Compute Engine Abstraction**:
- Abstract base class `ComputeEngine`
- Current: CUDA via CuPy, CPU via multiprocessing
- Future: ROCm for AMD, WebGPU for browsers, TPU
- Auto-detection and graceful degradation

**When implementing new transports/engines**:
- Inherit from abstract base class
- Implement all required methods
- Register in factory pattern
- Add to auto-detection logic
- Document limitations and status

## Code Quality Standards

### Error Handling

```python
# Good - Specific exception, graceful degradation
try:
    result = gpu_check_range(start, end)
except CUDAException as e:
    logger.warning(f"GPU failed: {e}, falling back to CPU")
    result = cpu_check_range(start, end)

# Bad - Silent failure
try:
    result = gpu_check_range(start, end)
except:
    result = {'counterexample': None}  # No fallback!
```

### Windows Compatibility

**Multiprocessing**: Always use guards for Windows:
```python
if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
```

**File Paths**: Use `pathlib.Path` for cross-platform paths:
```python
from pathlib import Path
keys_dir = Path("keys")
key_file = keys_dir / f"{username}_private_key.pem"
```

**Shell Commands**: Avoid platform-specific commands in Python:
```python
# Bad
os.system("rm -rf temp/")

# Good
import shutil
shutil.rmtree("temp/", ignore_errors=True)
```

### Return Format Consistency

**Verification functions must return dict**:
```python
def verify_range(start: int, end: int) -> dict:
    """
    Returns:
        dict: {
            'counterexample': None or int,
            'numbers_checked': int
        }
    """
```

**Worker functions should return dict, not tuples**:
```python
# Good
return {
    'counterexample': None,
    'numbers_checked': count
}

# Bad
return ('success', count)  # Inconsistent format
```

### Configuration Loading

**Handle nested JSON from validation**:
```python
# check_config_validity() returns {'config': {...}}
config_result = check_config_validity(config_file)
if config_result and 'config' in config_result:
    config = config_result['config']
else:
    config = default_config
```

**Always validate before accessing nested keys**:
```python
# Good
tuning = config.get('tuning', {})
cpu_workers = tuning.get('cpu_workers', None)

# Bad
cpu_workers = config['tuning']['cpu_workers']  # KeyError if missing
```

## Testing Requirements

### Before Committing Code

1. **Run diagnostics**: `python run_diagnostics.py`
2. **Run verification tests**: `python test_verification.py`
3. **Test user accounts**: `python test_user_accounts.py`
4. **Check multiprocessing on Windows**: Verify `if __name__ == '__main__'` guards

### Test Coverage

**Core verification**:
- CPU verification with small range (100 numbers)
- CPU verification with large range (10,000 numbers)
- GPU verification (if CUDA available)
- GPU fallback to CPU on error

**User accounts**:
- Account creation
- Account loading from private key
- Username uniqueness enforcement
- Multi-node registration

**IPFS coordinator**:
- Initialization
- Peer discovery (with graceful failure)
- Work assignment
- State publishing

### When Tests Fail

**Do not**:
- Ignore failing tests
- Comment out test code
- Skip error handling

**Instead**:
- Fix the root cause
- Add better error messages
- Improve graceful degradation
- Update tests if API changed

## Security Practices

### What to Document in SECURITY.md

**Implemented Features** (with ✅):
- Ed25519 digital signatures (specify library: `cryptography.hazmat.primitives`)
- SHA-256 hashing (specify: `hashlib.sha256`)
- IPFS content-addressing
- Worker identity via peer IDs

**Partial Implementations** (with 🚧):
- Multi-verifier consensus (framework exists, needs testing)
- Trust/reputation system (basic scoring, needs Byzantine testing)
- Anti-self-verification (design complete, enforcement partial)

**Known Vulnerabilities** (with ❌):
- Sybil attacks (no proof-of-work)
- Eclipse attacks (IPFS network partition)
- Trust score manipulation
- Consensus bypass (small network)

### Cryptographic Signing

**Always sign verification results**:
```python
from cryptography.hazmat.primitives.asymmetric import ed25519

# Sign
signature = private_key.sign(message.encode('utf-8'))

# Verify
try:
    public_key.verify(signature, message.encode('utf-8'))
    return True
except cryptography.exceptions.InvalidSignature:
    return False
```

**Never**:
- Skip signature verification
- Use weak hashing (MD5, SHA1)
- Store private keys in version control
- Hardcode cryptographic keys

## Version Control Practices

### Commit Messages

Use conventional commit format:
```
feat: add AMD ROCm compute engine abstraction
fix: resolve IPFS peer discovery list/dict handling
docs: update SECURITY.md with honest vulnerability assessment
refactor: extract network transport to abstract base class
test: add Windows multiprocessing guard tests
```

### What Not to Commit

- Private keys (`*.pem`, except test keys)
- Generated files (`gpu_tuning.json`, `diagnostic_report.json`)
- Build artifacts (`build/`, `dist/`, `*.pyc`)
- Local config (`collatz_config.json` with personal settings)
- Test account databases (`user_accounts.json` with real data)

### Git Workflow

1. **Feature branches**: `git checkout -b fix/peer-discovery`
2. **Test locally**: Run full test suite
3. **Commit logical units**: One fix per commit
4. **Clear messages**: Explain why, not just what
5. **Pull request**: Describe changes, link issues

## Community Feedback Integration

### Reddit Criticism (Lessons Learned)

**u/gandalfpc's feedback taught us**:
1. Placeholder code in core functions destroys credibility
2. Marketing claims without implementation are harmful
3. Security audit status must be stated explicitly
4. Versioning strategy must be documented upfront

**Velcar's feedback taught us**:
1. Computational verification can't prove Collatz (only disprove)
2. Educational/learning goals should be stated clearly
3. AI collaboration aspect should be transparent
4. Project is about distributed systems, not mathematical proof

### When Receiving Criticism

**Good response**:
1. Acknowledge the specific issue
2. Explain what was wrong
3. Show what you fixed (with links)
4. Thank the reviewer

**Bad response**:
1. Defensive arguing
2. Making excuses
3. Dismissing valid concerns
4. Ignoring the feedback

### Transparency About AI Development

**Be upfront**:
- "AI (Claude/Copilot) generates most code"
- "Human provides architecture and design decisions"
- "Community feedback drives improvements"
- "Learning project, not production system"

**Don't hide**:
- AI involvement in development
- Experimental nature of the project
- Limitations of current implementation
- Need for security audit

## Documentation Standards

### README.md

**Structure**:
1. Project status warning (ALPHA SOFTWARE)
2. What it is (technical description, not marketing)
3. Quick start (one-command install)
4. Current capabilities (implemented only)
5. Known limitations
6. Security status
7. How to contribute

**Language**:
- Technical, not promotional
- Honest about alpha status
- Separate implemented from planned
- Document known issues

### SECURITY.md

**Required sections**:
1. Current Implementation Status (with visual indicators)
2. Implemented Security Features (specific libraries/algorithms)
3. Partially Implemented (framework vs tested)
4. Known Vulnerabilities (specific attack vectors)
5. Threat Model
6. Responsible Disclosure Process
7. Security Audit Status (or lack thereof)
8. Invitation to Security Researchers

**Be specific**:
- "Ed25519 via cryptography library" not "cryptographic signatures"
- "SHA-256 content hashing" not "cryptographic proofs"
- "Honest majority trust model" not "Byzantine fault tolerant"

### VERSIONING.md

**Required sections**:
1. Semantic versioning rules
2. Current version and status
3. Version milestones roadmap
4. Protocol version headers
5. Backward compatibility strategy
6. Migration procedures
7. Deprecation policy
8. Cryptographic agility plan

**Versioning rules**:
- 0.x.x = alpha/beta (breaking changes allowed)
- 1.0.0 = stable API (semantic versioning enforced)
- Protocol versions in network messages
- 2 minor versions deprecation warning

## Auto-Update Mechanisms

### Docker Deployment

**docker-entrypoint.sh** must:
- Check for Git updates from GitHub
- Compare local vs remote commit
- Pull updates if available
- Reinstall Python dependencies if requirements.txt changed
- Log update status

**Environment variables**:
- `AUTO_UPDATE=true` (enable auto-updates)
- `UPDATE_BRANCH=master` (which branch to track)
- `UPDATE_INTERVAL=86400` (check interval in seconds)

### SystemD Service

**projectcollatz.service** must:
- Use `ExecStartPre=/opt/projectcollatz/update.sh`
- Run update script before starting worker
- Log updates to `/var/log/projectcollatz-update.log`
- Continue if update fails (don't break service)

### Install Scripts

**quick-install.sh** must:
- Check Python version (3.8+)
- Create virtual environment
- Install dependencies from requirements.txt
- Download and install IPFS
- Initialize IPFS repository
- Start IPFS daemon
- Test installation

**Error handling**:
- Detect missing dependencies
- Provide clear error messages
- Suggest fixes
- Exit with non-zero on failure

## Performance Considerations

### GPU Optimization

**Auto-tuning**:
- Create `gpu_tuning.json` on first run
- Test batch sizes: 1M, 10M, 100M
- Test thread configurations
- Save optimal settings
- Fall back to defaults if tuning fails

**Error handling**:
```python
try:
    config = get_gpu_config()
except Exception as e:
    logger.warning(f"GPU config failed: {e}, using defaults")
    config = default_gpu_config
```

### CPU Optimization

**Multiprocessing**:
- Use `mp.Pool` for parallel verification
- Default to `min(cpu_count(), 8)` workers
- Chunk work into manageable ranges (10,000 numbers per chunk)
- Handle worker failures gracefully

**Memory management**:
- Avoid loading entire ranges into memory
- Stream results
- Clean up worker pools

## Deployment Platforms

### Supported Platforms

**Tested and supported**:
- Windows x64 (Python 3.8+)
- Linux x64 (Python 3.8+)
- Linux ARM64 (Raspberry Pi, SBC)
- macOS Intel/M1/M2 (Python 3.8+)
- Docker multi-arch

**Test on**:
- Windows 10/11
- Ubuntu 20.04+
- Raspberry Pi OS
- macOS 11+

### Platform-Specific Issues

**Windows**:
- Requires multiprocessing guards
- Use PowerShell for install script
- Path separators via `pathlib.Path`

**Linux**:
- systemd service for auto-start
- Update script with git pulls
- IPFS binary in `/usr/local/bin`

**Raspberry Pi**:
- ARM64/ARM32 binaries
- Lower default batch sizes
- CPU-only mode (no GPU)

**macOS**:
- M1/M2 compatibility
- Homebrew IPFS installation
- Python from official installer

## Project Goals & Philosophy

### What This Project IS

1. **Educational**: Learn distributed systems through AI-assisted development
2. **Collaborative**: Human architecture + AI implementation + community feedback
3. **Transparent**: Honest about limitations, alpha status, AI involvement
4. **Experimental**: Test distributed computing concepts with real workload
5. **Open**: Invite criticism, security review, contributions

### What This Project IS NOT

1. **Production System**: Alpha software, expect bugs and breaking changes
2. **Mathematical Proof**: Computation can't prove Collatz, only find counterexample
3. **Commercial Product**: Educational/research project, CC BY-NC-SA license
4. **Security Audited**: No independent audit (yet), honest about vulnerabilities
5. **Finished**: Ongoing development, always improving based on feedback

### Success Metrics

**Technical**:
- All core verification code has real implementations
- No critical placeholder functions
- Tests pass on all supported platforms
- Documentation matches implementation status

**Community**:
- Honest response to criticism
- Security researchers welcome
- Contributions from diverse hardware
- Educational value for distributed systems learners

**Development**:
- AI generates code, human reviews and designs
- Feedback loop from community improves architecture
- Transparent about AI collaboration
- Iterative improvement based on real usage

## Summary for AI Agents

When contributing to this project:

1. **Never add placeholder code to core verification, consensus, or security functions**
2. **Always document implementation status honestly (Implemented/Partial/Planned)**
3. **Use technical language, not marketing buzzwords**
4. **Test on Windows (multiprocessing guards required)**
5. **Return dict format from verification functions, not tuples**
6. **Handle errors gracefully with fallbacks**
7. **Update documentation to match code reality**
8. **No emoji overuse in technical docs (status indicators OK)**
9. **Be transparent about AI development and limitations**
10. **Welcome criticism and use it to improve**

This is an educational AI-collaborative project about learning distributed systems. Honesty about capabilities and limitations builds more credibility than marketing claims.

---

**Last Updated**: October 28, 2025
**Status**: Active development, alpha stage
**Maintainer**: Jay Wenden (Jaylouisw)
**AI Assistants**: Claude (Anthropic), GitHub Copilot
