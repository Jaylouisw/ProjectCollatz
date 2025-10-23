# Collatz Engine

A highly optimized GPU-accelerated engine for exploring the Collatz Conjecture, featuring adaptive auto-tuning and hybrid CPU+GPU architecture.

## Features

- **Hybrid CPU+GPU architecture** - Maximizes throughput using CuPy for CUDA acceleration
- **Adaptive auto-tuner** - Dynamically optimizes GPU parameters for peak performance
- **Efficient odd-only checking** - Skips even numbers (trivial cases)
- **Persistent state** - Resume capability with checkpoint system
- **Real-time monitoring** - Split-screen display for checker and tuner
- **Multi-stage optimization** - Binary search + fine-tuning + progressive refinement

## Performance

Current benchmarks on mid-range GPU (6GB VRAM):
- **~10 billion odd/s** (~20 billion effective/s)
- **572+ trillion numbers** tested over continuous runtime
- Auto-tuner adapts to any CUDA-capable GPU

## Requirements

- CUDA-capable GPU with recent drivers
- Python 3.8+
- CuPy (CUDA acceleration library)

## Installation

```bash
# Install dependencies
pip install cupy-cuda12x  # or cupy-cuda11x for older CUDA versions

# Clone repository
git clone <your-repo-url>
cd CollatzEngine
```

## Usage

### Option 1: Automated Launcher (Recommended)

Run both the hybrid checker and auto-tuner together with split-screen display:

```bash
python launcher.py
```

### Option 2: Benchmark Mode

For automated performance testing and results collection:

```bash
python benchmark.py
```

This will:
- Collect system specifications automatically
- Run optimization for a specified duration
- Save all results to a JSON file

### Option 3: Manual Execution

Run components separately:

```bash
# Terminal 1 - Hybrid Checker
python collatz_hybrid.py

# Terminal 2 - Auto-Tuner (start after 60 seconds)
python auto_tuner.py
```

## How It Works

### Hybrid Checker (`collatz_hybrid.py`)
- Tests odd numbers for Collatz convergence
- Uses GPU for parallel computation
- Maintains persistent state across sessions
- Reports real-time performance metrics

### Auto-Tuner (`auto_tuner.py`)
- **Stage 1**: Binary search for optimal parameters (60s quick tests)
- **Stage 2**: Fine-tuning around best configurations (2-min tests)
- **Stage 3**: Progressive refinement until convergence

Optimizes:
- Batch size
- Threads per block
- Work multiplier
- Blocks per streaming multiprocessor

### Launcher (`launcher.py`)
- Manages both processes automatically
- Provides unified split-screen display
- Handles graceful shutdown

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

[Choose your license]

## Acknowledgments

Built with CuPy for CUDA acceleration. Thanks to all GPU benchmark volunteers!
