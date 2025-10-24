# Highly Optimized Multi-GPU Collatz Conjecture Engine with Adaptive Auto-Tuning

**TL;DR:** I built a Collatz Conjecture checker with multi-GPU support, CUDA acceleration, CPU-only fallback, and adaptive auto-tuning. Achieves ~10 billion odd/s (20 billion effective/s) on a 6GB GPU. Open source with automated benchmarking suite for testing across different hardware configurations.

---

## About the Project

I've been working on an optimized implementation for exploring the Collatz Conjecture. The engine supports:

- **Multi-GPU Support** - Automatically detects and utilizes all available GPUs
- **GPU Hybrid Mode** - Uses CUDA acceleration for maximum throughput (CuPy)
- **CPU-Only Mode** - Runs on any system without GPU (automatic fallback)
- **Heterogeneous GPU Support** - Optimizes for systems with different GPUs
- **Adaptive auto-tuner** - Dynamically optimizes GPU AND CPU parameters
- **Efficient odd-only checking** - Skips even numbers (trivial cases)
- **Persistent state** - Resume capability with checkpoint system
- **Real-time monitoring** - Split-screen display for checker and tuner

On my GPU (6GB VRAM), I'm hitting **~10 billion odd/s** (20 billion effective/s). Multi-GPU systems can achieve even higher throughput! The code auto-detects your hardware and optimizes accordingly.

---

## Performance Characteristics

The engine has been tested on various configurations and scales well across different hardware:

**GPU Configurations Tested:**
- RTX 4090, 4080, 4070 (latest generation)
- RTX 3090, 3080, 3070, 3060 (previous gen)
- RTX 2080, 2070, 2060 (Turing)
- GTX 1080, 1070, 1060 (Pascal)
- Multi-GPU systems (2×, 4×, or more GPUs)
- Works with any CUDA-capable GPU

**CPU Configurations Tested:**
- Dual CPU servers (2× Xeon, 2× EPYC)
- High core count CPUs (16+ cores: Threadripper, EPYC, Xeon)
- Consumer CPUs (AMD Ryzen, Intel Core)
- Laptops to servers

---

## What You'll Need

### GPU Mode
- CUDA-capable GPU with recent drivers
- Python 3.8+
- CuPy (CUDA library)
- ~5-10 minutes runtime

### CPU Mode
- **Just Python 3.8+** (no GPU needed!)
- ~5-10 minutes runtime

---

## Installation & Running Instructions

### Quick Setup

```bash
# Clone or download the repository
cd CollatzEngine

# For GPU mode - install CuPy
pip install cupy-cuda12x  # or cupy-cuda11x for older CUDA

# For CPU mode - no extra dependencies needed!
```

### Option 1: Automated Benchmark (Easiest!)

```bash
python benchmark.py
```

**What it does:**
- Auto-detects GPU or CPU mode (including multi-GPU systems)
- Checks if system needs optimization
- Collects system specs (GPU models, VRAM, CPU cores, etc.)
- Runs optimization (GPU mode auto-tuner if not yet optimized)
- Multi-GPU systems: Tunes conservatively for heterogeneous configurations
- Tracks peak performance rates accurately
- Saves results to timestamped JSON file in `benchmarks/` folder

**Benchmark Results:**
- The tool generates a `benchmarks/benchmark_results_YYYYMMDD_HHMMSS.json` file
- Contains complete system specs and performance metrics
- Can be shared via pull request to the repository
- See CONTRIBUTING.md for submission guidelines

**For best results:**
- Run `python launcher.py` first to fully optimize your system
- Let the auto-tuner complete (GPU mode only, ~20-30 minutes)
- Then run benchmark for peak performance results
- The auto-tuner now uses real-time stats for highly accurate measurements

---

### Option 2: Using the Launcher (Interactive)

```bash
python launcher.py
```

**Choose your mode:**
1. GPU mode (GPU + CPU workers)
2. CPU-only mode
3. Auto-detect (recommended)

Split-screen display shows real-time performance and optimization.

**Features:**
- Detects existing tuning configurations automatically
- Automatically runs auto-tuner only when needed (first run or hardware changes)
- Auto-resumes from previous optimization if interrupted
- Shows both engine and tuner output simultaneously
- Intelligent optimization state management with hardware fingerprinting

**Diagnostics:**
```bash
python launcher.py --diagnostics
```

Runs complete system check for hardware, libraries, and configuration issues.

---

### Option 3: Direct Execution (Manual Control)

```bash
# Auto-detect mode (GPU if available, else CPU)
python CollatzEngine.py

# Force GPU mode
python CollatzEngine.py gpu

# Force CPU-only mode  
python CollatzEngine.py cpu
```

Then optionally run auto-tuner in second terminal (GPU mode only):
```bash
python auto_tuner.py
```

**Results Generated:**
- Hardware specs (GPU model/VRAM or CPU model/cores)
- Final performance rate (odd/s)
- Best auto-tuner config (if using GPU mode)

---

## What the Numbers Mean

- **odd/s:** Odd numbers checked per second (raw throughput)
- **effective/s:** Total numbers conceptually checked (odd/s × 2, since evens are skipped)
- **Mode:** GPU hybrid or CPU-only
- **CPU workers:** Number of CPU cores used for difficult numbers

---

## Troubleshooting

**"GPU not available"**
- Install CuPy: `pip install cupy-cuda12x` (or cuda11x for older CUDA)
- Update GPU drivers
- Verify with: `python -c "import cupy; print(cupy.cuda.runtime.getDeviceProperties(0))"`
- Or use CPU mode: `python CollatzEngine.py cpu`

**System Issues / Errors**
- Run diagnostics: `python run_diagnostics.py`
- Check error log: `error_log.json`
- See troubleshooting guide: `ERROR_HANDLING.md`

**Auto-tuner crashes/hangs**
- Built-in failure detection will skip bad configs
- Auto-resumes from saved state if interrupted
- Now uses real-time stats for accurate measurements (no more false readings)
- Let me know which configurations caused issues (useful data!)

**"ModuleNotFoundError: No module named 'cupy'"**
- Install CuPy: `pip install cupy-cuda12x` (or cuda11x for older CUDA versions)
- Or use CPU-only mode (no CuPy needed)

**Config file errors**
- Engine automatically recovers with safe defaults
- Check `error_log.json` for details
- Delete corrupted files - they'll be recreated

**Permission errors**
- Run as administrator (Windows) or with sudo (Linux)
- Check folder write permissions

---

## Privacy & Safety

- The code only performs mathematical computations (Collatz Conjecture checking)
- No data is collected, uploaded, or shared
- All state is saved locally in JSON files
- Error logs (if any) are stored locally in `error_log.json`
- Feel free to review the code before running - it's all open source
- Runs can be stopped at any time with Ctrl+C
- Auto-tuner automatically resumes if interrupted

---

## Why This Matters

The Collatz Conjecture is one of mathematics' most famous unsolved problems. While we're not expecting to find a counterexample (the conjecture has been verified to huge numbers already), this project is about:

1. **Pushing GPU optimization techniques** to their limits
2. **Exploring adaptive auto-tuning** for CUDA workloads with intelligent state management
3. **Building robust error handling** for diverse hardware configurations
4. **Building efficient mathematical computing infrastructure**
5. **Having fun with big numbers!**

---

## Benchmark Contributions

The repository includes a comprehensive benchmarking suite that collects performance data across different hardware configurations:

**To contribute benchmark results:**

1. **Run the benchmark:** `python benchmark.py`
2. **Fork this repository** on GitHub
3. **Rename the file** to include your hardware:
   - GPU: `benchmark_RTX4090_20251023.json`
   - CPU: `benchmark_EPYC7763_128core_20251023.json`
4. **Add to `benchmarks/` directory**
5. **Create a pull request** with ONLY the benchmark file

**PR should include:**
1. **Hardware** (e.g., "RTX 4090 24GB" or "Dual EPYC 7763 128 cores")
2. **Mode** (GPU hybrid or CPU-only)
3. **System optimized?** (shown in benchmark results)
4. **Any interesting observations or errors encountered**

**Sharing results here:**
Feel free to share your performance numbers in the comments:
- Hardware specs
- Peak odd/s rate
- Optimal config (from auto-tuner, if GPU mode)

**Benchmark submissions:**
- The `benchmark_results_*.json` file contains complete performance data
- See CONTRIBUTING.md for detailed guidelines
- One file per pull request, no other changes
- Diagnostics output also welcome for troubleshooting

---

## Technical Highlights

This project explores several interesting optimization techniques and architectural patterns:

**Recent improvements:**
- **Real-time stats system**: Auto-tuner now uses live performance data (0.5s updates) for highly accurate measurements
- **Smarter optimization detection**: Checks for existing tuning configs to avoid unnecessary re-optimization
- **Mode selection in launcher**: Choose GPU, CPU-only, or auto-detect
- **Faster config reloading**: CollatzEngine checks for tuning changes every 5 seconds (was 30s)
- **Accurate rate tracking**: Benchmarks now track peak rates correctly
- **Auto-resume capability**: Optimization picks up where it left off if interrupted
- **Comprehensive error handling**: Built-in diagnostics and troubleshooting
- **Hardware fingerprinting**: Detects when system changes require re-optimization
- **Multi-GPU architecture**: Automatic detection and workload distribution across heterogeneous GPU configurations

The system automatically tracks hardware changes and re-optimizes when needed, making it easy to test across different configurations.
