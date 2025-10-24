# Collatz Engine

A highly optimized GPU-accelerated engine for exploring the Collatz Conjecture, featuring adaptive auto-tuning, hybrid CPU+GPU architecture, and CPU-only fallback mode.

📚 **New to this project?** Start with [QUICK_START.md](QUICK_START.md) | **All documentation:** [DOCUMENTATION.md](DOCUMENTATION.md)

## Features

- **Hybrid CPU+GPU architecture** - Maximizes throughput using CuPy for CUDA acceleration
- **CPU-only mode** - Runs on systems without GPU (automatic fallback)
- **Adaptive auto-tuner** - Dynamically optimizes GPU and CPU parameters for peak performance
- **Comprehensive error handling** - Catches hardware issues, missing libraries, driver problems
- **Efficient odd-only checking** - Skips even numbers (trivial cases)
- **Persistent state** - Resume capability with checkpoint system
- **Real-time monitoring** - Split-screen display for checker and tuner
- **Multi-stage optimization** - Binary search + fine-tuning + progressive refinement
- **Contribution tracking** - Track and share verification progress across a distributed network
- **System diagnostics** - Built-in health checks and troubleshooting

## Performance

Current benchmarks on mid-range GPU (6GB VRAM):
- **~10 billion odd/s** (~20 billion effective/s)
- **572+ trillion numbers** tested over continuous runtime
- Auto-tuner adapts to any CUDA-capable GPU or CPU-only system

## Requirements

### GPU Mode (Recommended)
- CUDA-capable GPU with recent drivers
- Python 3.8+
- CuPy (CUDA acceleration library)

### CPU Mode (Fallback)
- Python 3.8+
- No GPU required

## Installation

```bash
# For GPU mode - install CuPy
pip install cupy-cuda12x  # or cupy-cuda11x for older CUDA versions

# Clone repository
git clone <your-repo-url>
cd CollatzEngine
```

**First-time users:** See [QUICK_START.md](QUICK_START.md) for step-by-step instructions.

**System check:**
```bash
python run_diagnostics.py  # Verify your system is ready
```

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
- **GPU Mode**: Tests odd numbers using CUDA acceleration with GPU batching
- **CPU Mode**: Pure CPU implementation with multiprocessing (uses GPU for batching if available)
- Maintains persistent state across sessions
- Reports real-time performance metrics
- Automatically falls back to CPU mode if GPU unavailable

### Auto-Tuner (`auto_tuner.py`) - GPU Mode Only
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
