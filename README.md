# Collatz Engine

A highly optimized GPU-accelerated engine for exploring the Collatz Conjecture, featuring adaptive auto-tuning, hybrid CPU+GPU architecture, and **fully decentralized verification network**.

📚 **New to this project?** Start with [QUICK_START.md](QUICK_START.md) | **All documentation:** [DOCUMENTATION.md](DOCUMENTATION.md)

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

### Raspberry Pi:
Download pre-built image from [Releases](https://github.com/Jaylouisw/ProjectCollatz/releases)

**→ See [DISTRIBUTED_QUICKREF.md](DISTRIBUTED_QUICKREF.md) for complete installation guide!**

---

## Features

### Local Verification
- **Multi-GPU support** - Automatically detects and uses all available GPUs in parallel
- **Hybrid CPU+GPU architecture** - Maximizes throughput using CuPy for CUDA acceleration
- **CPU-only mode** - Runs on systems without GPU (automatic fallback)
- **Adaptive auto-tuner** - Dynamically optimizes GPU and CPU parameters for peak performance
- **Heterogeneous GPU support** - Works with different GPU models simultaneously
- **Comprehensive error handling** - Catches hardware issues, missing libraries, driver problems
- **Efficient odd-only checking** - Skips even numbers (trivial cases)
- **Persistent state** - Resume capability with checkpoint system
- **Real-time monitoring** - Split-screen display for checker and tuner
- **Multi-stage optimization** - Binary search + fine-tuning + progressive refinement
- **System diagnostics** - Built-in health checks and troubleshooting

### Distributed Network
- **🌐 Fully decentralized** via IPFS (no central server, runs forever)
- **🔐 Cryptographic proofs** with Ed25519 signatures (tamper-proof)
- **👥 Multi-worker consensus** (3+ workers verify each range)
- **⭐ Trust & reputation system** with automatic bad-actor detection
- **🛡️ Byzantine fault tolerance** via redundant verification
- **📊 Public verification records** stored permanently on IPFS
- **🎉 Counterexample celebration** with automatic network-wide notification
- **🗳️ Democratic voting** for network continuation decisions
- **🏆 IPFS leaderboard** showing top contributors
- **👤 User accounts** with persistent identity across nodes
- **🔒 Random work assignment** prevents collusion attacks
- **🐳 Docker support** for easy deployment
- **🥧 Raspberry Pi support** with pre-built images

**→ See [DISTRIBUTED.md](DISTRIBUTED.md) for full details on joining the distributed network!**

## Performance

Current benchmarks on mid-range GPU (6GB VRAM):
- **~10 billion odd/s** (~20 billion effective/s)
- **572+ trillion numbers** tested over continuous runtime
- Auto-tuner adapts to any CUDA-capable GPU or CPU-only system

## Requirements

### GPU Mode (Recommended)
- One or more CUDA-capable GPUs with recent drivers
- Python 3.8+
- CuPy (CUDA acceleration library)
- **Multi-GPU**: Automatically detected and utilized (scales linearly)

### CPU Mode (Fallback)
- Python 3.8+
- No GPU required

## Manual Installation

### For Distributed Network:
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

### For Local GPU Verification:
```bash
# Install CuPy (GPU acceleration)
pip install cupy-cuda12x  # or cupy-cuda11x for older CUDA

# Clone repository
git clone https://github.com/Jaylouisw/ProjectCollatz.git
cd ProjectCollatz

# Run the engine
python launcher.py
```

### For CPU-Only Mode:
```bash
# No additional dependencies needed!
git clone https://github.com/Jaylouisw/ProjectCollatz.git
cd ProjectCollatz
python CollatzEngine.py cpu
```

**First-time users:** See [QUICK_START.md](QUICK_START.md) for step-by-step instructions.

**System check:**
```bash
python run_diagnostics.py  # Verify your system is ready
```

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

## Usage

### Option 1: Automated Launcher (Recommended)

Run the engine with intelligent optimization management:

```bash
python launcher.py
```

The launcher will prompt you to choose:
1. **GPU mode** - GPU + CPU workers (best performance)
2. **CPU-only mode** - Pure multiprocessing
3. **Auto-detect** - Automatically selects based on hardware

**Features:**
- Detects existing tuning configurations (no unnecessary re-optimization)
- Automatically runs auto-tuner only when needed
- Auto-resumes from saved state if interrupted
- Split-screen display (engine + tuner)
- Smart hardware fingerprinting

**First Run:** System will optimize automatically if GPU mode selected (~20-30 minutes)

**Subsequent Runs:** Uses existing tuning, skips optimization unless hardware changed

**System Diagnostics:**
```bash
python launcher.py --diagnostics
```

Checks for hardware issues, missing libraries, driver problems, etc.

### Option 2: Direct Execution

Run the Collatz Engine directly:

```bash
# Auto-detect mode (GPU if available, otherwise CPU)
python CollatzEngine.py

# Force GPU hybrid mode
python CollatzEngine.py gpu

# Force CPU-only mode
python CollatzEngine.py cpu
```

**Note:** Direct execution skips auto-tuner. For best performance, use launcher first.

### Option 3: Benchmark Mode

For automated performance testing and results collection:

```bash
python benchmark.py
```

**Recommendation:** Run `launcher.py` first to optimize, then run benchmark for accurate results.

```bash
python benchmark.py
```

This will:
- Auto-detect GPU or CPU mode
- Collect system specifications automatically
- Run optimization for a specified duration (GPU mode includes auto-tuner)
- Save all results to a JSON file

## How It Works

### Collatz Engine (`CollatzEngine.py`)
- **Multi-GPU Mode**: Automatically detects and uses all GPUs in parallel with workload distribution
- **GPU Mode**: Tests odd numbers using CUDA acceleration with GPU batching
- **CPU Mode**: Pure CPU implementation with multiprocessing
- **Heterogeneous support**: Works with different GPU models (uses lowest VRAM as baseline)
- Maintains persistent state across sessions
- Reports real-time performance metrics
- Automatically falls back to CPU mode if GPU unavailable

### Auto-Tuner (`auto_tuner.py`) - GPU Mode Only
- **Multi-GPU tuning**: Detects all GPUs and tunes for optimal multi-GPU performance
- **Conservative tuning**: Uses lowest VRAM GPU as baseline for heterogeneous systems
- **Real-time performance measurement**: Reads live stats every 0.5 seconds for accurate rate calculation
- **Stage 1**: Binary search for optimal parameters (60s quick tests)
- **Stage 2**: Fine-tuning around best configurations (2-min tests)
- **Stage 3**: Progressive refinement until convergence
- **Auto-resume**: Automatically picks up where it left off if interrupted
- **Smart invocation**: Only runs when needed (first run, hardware changes, or incomplete optimization)
- **Precise measurements**: Uses session-based counters and actual timestamps for accuracy

Optimizes:
- Batch size (future-proofed for 100+ years of GPU evolution)
- Threads per block
- Work multiplier
- Blocks per streaming multiprocessor
- CPU worker count (1-1024+ cores supported)

### Optimization State Management (`optimization_state.py`)
- **Hardware fingerprinting**: SHA256 hash of GPU+CPU specs
- **Intelligent detection**: Checks for existing gpu_tuning.json to avoid re-optimization
- **State persistence**: Tracks completion across sessions
- **Hardware change detection**: Re-optimizes when hardware changes
- **Benchmark tracking**: Records when final benchmarks are completed

### Launcher (`launcher.py`)
- **Mode selection**: Choose GPU, CPU-only, or auto-detect
- Manages both engine and auto-tuner processes automatically
- Provides unified split-screen display
- Handles graceful shutdown
- **Smart optimization**: Only runs tuner when needed, uses existing configs when available
- **Pre-flight checks**: Validates libraries and permissions
- **Diagnostics mode**: `--diagnostics` flag for system health check

### Error Handler (`error_handler.py`)
- **Comprehensive logging**: All errors saved to `error_log.json`
- **System diagnostics**: Hardware, library, and config validation
- **Automatic recovery**: Falls back to safe defaults on errors
- **Detailed reports**: Full stack traces with system context
- **Hardware checks**: GPU availability, CUDA runtime, library validation

### Contribution Tracker (`contribution_tracker.py`)
- Records verification contributions from each user
- Tracks highest values proven by each contributor
- Creates a leaderboard of all participants
- Export and merge contributions from multiple users
- Build a distributed verification network

## Contribution Tracking

The engine automatically tracks your contributions to help build a distributed verification network:

### First Run Setup
On first run, you'll be prompted to set up your contributor profile:
- Choose a username/alias (or use auto-generated ID)
- Optional: Enter your GPU name
- Your contributions are tracked locally

### View Leaderboard
```bash
python contribution_tracker.py leaderboard
```

Shows:
- Total contributors
- Numbers tested by each user
- Runtime contributions
- Highest values proven

### Share Your Contributions
```bash
python contribution_tracker.py export
```

Creates a shareable JSON file with your verification results.

### Merge Contributions
```bash
python contribution_tracker.py merge contributions_export.json
```

Combine contributions from multiple users to build a global leaderboard.

### Privacy
- Machine IDs are hashed for privacy
- You choose your public username
- Contribution files can be shared to prove verification ranges
- User profile stays local unless you choose to share

## Configuration Files

- `collatz_config.json` - Main checker configuration and progress state
- `gpu_tuning.json` - Current GPU optimization settings (auto-tuner output)
- `realtime_stats.json` - Live performance stats (updates every 0.5s for auto-tuner accuracy)
- `autotuner_state.json` - Auto-tuner resume state (for interrupted sessions)
- `optimization_state.json` - Hardware fingerprint and optimization completion status
- `error_log.json` - Error history with diagnostics (automatic logging)
- `diagnostic_report.json` - System health check results
- `user_profile.json` - Contribution tracker profile (optional)

**Note:** All state files are in `.gitignore` - they're user-specific and won't be committed.

## Troubleshooting

### Run System Diagnostics

Check for hardware issues, missing libraries, or driver problems:

```bash
python run_diagnostics.py
```

Or through the launcher:

```bash
python launcher.py --diagnostics
```

This will check:
- Required Python libraries
- GPU availability and status
- File permissions
- Configuration file validity
- System specifications

### Error Logging

All errors are automatically logged to `error_log.json` with:
- Error type and message
- Full stack traces
- System information
- Timestamps

For detailed troubleshooting guide, see [ERROR_HANDLING.md](ERROR_HANDLING.md)

### Common Issues

**GPU Not Detected:**
- Install CuPy: `pip install cupy-cuda12x`
- Update GPU drivers
- Or use CPU mode: `python CollatzEngine.py cpu`

**Config File Errors:**
- Engine automatically recovers with defaults
- Check `error_log.json` for details

**Permission Errors:**
- Run as administrator (Windows)
- Check folder write permissions

## Contributing

Benchmark results from different GPUs are welcome! See `REDDIT_POST.md` for volunteer information.

## What the Numbers Mean

- **odd/s**: Odd numbers checked per second (raw GPU throughput)
- **effective/s**: Total conceptual numbers checked (odd/s × 2, since evens are trivial)
- **Highest proven**: Largest starting value verified to reach 1
- **Total tested**: Cumulative numbers checked across all runs

## About the Collatz Conjecture

The Collatz Conjecture states that for any positive integer:
- If even, divide by 2
- If odd, multiply by 3 and add 1
- Repeat until you reach 1

This simple rule has been verified for enormous numbers but remains unproven mathematically.

## Technical Optimizations

This engine prioritizes **verification integrity** over raw speed. All optimizations maintain rigorous checking while maximizing GPU efficiency.

### ✅ Optimizations Applied

#### GPU Kernel (Primary Performance Gains)

**1. Branchless Convergence Checks (20-40% speedup)**
```cuda
// Before: Multiple nested if statements causing warp divergence
if (num_high == 0) {
    if (num_low == 1) { return; }
}

// After: Bitwise operations, single exit point
int is_one = (num_high == 0) & (num_low == 1);
int below_proven = (num_high < proven_high) | ((num_high == proven_high) & (num_low <= proven_low));
if (is_one | below_proven | below_start) { return; }
```
**Impact:** Reduced warp divergence, better GPU utilization
**Trade-off:** None - same verification rigor

**2. Simplified Loop Structure**
- Removed manual 4x unrolling (243 lines → 100 lines)
- Let compiler optimize with `#pragma unroll 1`
- Cleaner, more maintainable code
**Impact:** ~10% speedup from compiler optimizations
**Trade-off:** None

**3. Power-of-2 Cycle Check Interval**
- Changed from 100 to 128 steps
- Fast bitwise modulo: `(steps & 127)` vs `(steps % 100)`
**Impact:** Minor speedup in cycle detection
**Trade-off:** None

**4. Trailing Zero Optimization**
```cuda
// Skip multiple divisions at once
int zeros = __ffsll(num_low) - 1;
num_low = __funnelshift_r(num_high, num_low, zeros);
```
**Impact:** Handles even numbers efficiently
**Trade-off:** None

**5. 128-bit Arithmetic**
- Full support for numbers > 2^64
- Uses two 64-bit integers with carry handling
**Impact:** No precision loss for large numbers
**Trade-off:** Slightly more complex but necessary

#### CPU Implementation

**1. Lazy Cycle Detection**
- Check for loops every 50 steps instead of every step
- Uses set for visited numbers
**Impact:** ~3x faster than checking every step
**Trade-off:** Could miss very short cycles (acceptable)

**2. Trailing Zero Optimization**
```python
tz = (n & -n).bit_length() - 1
n >>= tz  # Skip k divisions at once
```
**Impact:** Efficient even number handling
**Trade-off:** None

**3. Multi-core Parallelism**
- Uses all CPU cores at low priority
- Independent workers process number ranges
**Impact:** Linear scaling (8 cores = 8x speedup)
**Trade-off:** None

### ❌ Optimizations Intentionally Avoided

#### 1. Odd-to-Odd Skipping (4n+1 relation)
```python
# NOT IMPLEMENTED:
# Jump from odd to odd: n → (3n+1)/2 → (3((3n+1)/2)+1)/2 ...
# Skip intermediate even values entirely
```
**Why avoided:**
- Skips intermediate value verification
- Could miss certain counterexample types
- Compromises cycle detection rigor
- **Our priority:** Rigorous verification > speed

**Source:** Reddit r/Collatz community feedback

#### 2. Multi-Step Batching with 3^m
```python
# NOT IMPLEMENTED:
# n = ((n * 3^m - (3^m - 1)) >> (2*m)) + 1
# Process m steps in one operation based on bit patterns
```
**Why avoided:**
- Skips m intermediate checks
- Mathematically equivalent but verification-incomplete
- Pattern matching adds complexity
- **GPU already 1000x faster than CPU anyway**

**Source:** Reddit mod 8 traversal discussion

#### 3. NumPy/SIMD Vectorization
```python
# TESTED BUT NOT ADOPTED:
# Process 8 numbers simultaneously with NumPy
n = np.array([n1, n2, n3, n4, n5, n6, n7, n8])
```
**Why avoided:**
- NumPy overhead > benefits (2.3x SLOWER)
- Sequential dependencies prevent true SIMD gains
- Branch divergence negates parallelism
- **GPU approach is superior**

**Benchmark results:**
- Scalar: 1,130,000 numbers/sec
- NumPy SIMD: 490,000 numbers/sec
- GPU: 10,000,000,000 numbers/sec

**Source:** Internal testing (see `simd_collatz.py`)

#### 4. Tensor Cores (AI Hardware)
**Why not applicable:**
- Tensor Cores designed for matrix multiplication
- Collatz needs scalar integer arithmetic
- No INT128 support in Tensor Cores
- Sequential dependencies prevent matrix operations
- **Wrong hardware for this workload**

#### 5. (3n+1)/2 Combining
```python
# TESTED BUT NO BENEFIT:
# n = ((n << 1) + n + 1) >> 1  # Combine 3n+1 with /2
```
**Why reverted:**
- Trailing zero optimization already handles this
- No measurable performance gain
- Original code equally efficient

### Performance Summary

**Effective Optimizations:**
1. GPU branchless operations: **+20-40%**
2. Multi-GPU scaling: **Linear (2x, 4x, etc.)**
3. CPU multi-core: **Linear scaling**
4. Adaptive auto-tuner: **2-3x improvement**

**Avoided Optimizations:**
1. Odd-to-odd: Would give **5x speed** but compromise verification
2. Multi-step batching: Would give **2-3x speed** but skip checks
3. SIMD: Actually **2x slower** due to overhead

**Design Philosophy:**
> "Better to verify 10 billion numbers/sec rigorously than 50 billion numbers/sec with gaps."

**See Also:**
- [KERNEL_OPTIMIZATION_NOTES.md](KERNEL_OPTIMIZATION_NOTES.md) - Detailed optimization analysis
- [simd_collatz.py](simd_collatz.py) - SIMD investigation results

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
