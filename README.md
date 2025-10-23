# Collatz Engine

A highly optimized GPU-accelerated engine for exploring the Collatz Conjecture, featuring adaptive auto-tuning, hybrid CPU+GPU architecture, and CPU-only fallback mode.

## Features

- **Hybrid CPU+GPU architecture** - Maximizes throughput using CuPy for CUDA acceleration
- **CPU-only mode** - Runs on systems without GPU (automatic fallback)
- **Adaptive auto-tuner** - Dynamically optimizes GPU and CPU parameters for peak performance
- **Efficient odd-only checking** - Skips even numbers (trivial cases)
- **Persistent state** - Resume capability with checkpoint system
- **Real-time monitoring** - Split-screen display for checker and tuner
- **Multi-stage optimization** - Binary search + fine-tuning + progressive refinement
- **Contribution tracking** - Track and share verification progress across a distributed network

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

## Usage

### Option 1: Automated Launcher (Recommended)

Run both the checker and auto-tuner together with split-screen display:

```bash
python launcher.py
```

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

### Option 3: Benchmark Mode

For automated performance testing and results collection:

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
- **Stage 1**: Binary search for optimal parameters (60s quick tests)
- **Stage 2**: Fine-tuning around best configurations (2-min tests)
- **Stage 3**: Progressive refinement until convergence

Optimizes:
- Batch size
- Threads per block
- Work multiplier
- Blocks per streaming multiprocessor
- CPU worker count (for difficult numbers)

### Launcher (`launcher.py`)
- Manages both processes automatically
- Provides unified split-screen display
- Handles graceful shutdown

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

- `collatz_config.json` - Main checker configuration
- `gpu_tuning.json` - Current GPU optimization settings
- `autotuner_state.json` - Auto-tuner resume state

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
