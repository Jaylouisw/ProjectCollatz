# Looking for GPU & CPU Volunteers to Benchmark Collatz Conjecture Engine

**TL;DR:** I've built a highly optimized Collatz Conjecture checker with GPU acceleration (CUDA) and CPU-only fallback, plus adaptive auto-tuning. Looking for volunteers with ANY hardware (GPUs, high-core-count CPUs, or both) to help benchmark performance across different systems.

---

## About the Project

I've been working on an optimized implementation for exploring the Collatz Conjecture. The engine supports:

- **GPU Hybrid Mode** - Uses CUDA acceleration for maximum throughput (CuPy)
- **CPU-Only Mode** - Runs on any system without GPU (automatic fallback)
- **Adaptive auto-tuner** - Dynamically optimizes GPU AND CPU parameters
- **Efficient odd-only checking** - Skips even numbers (trivial cases)
- **Persistent state** - Resume capability with checkpoint system
- **Real-time monitoring** - Split-screen display for checker and tuner

On my GPU (6GB VRAM), I'm hitting **~10 billion odd/s** (20 billion effective/s). The code auto-detects your hardware and optimizes accordingly.

---

## What I'm Looking For

**GPU benchmarks** AND **CPU benchmarks** - I want to understand performance across the full hardware spectrum!

**GPUs of interest:**
- RTX 4090, 4080, 4070 (latest generation)
- RTX 3090, 3080, 3070, 3060 (previous gen)
- RTX 2080, 2070, 2060 (Turing)
- GTX 1080, 1070, 1060 (Pascal)
- A100, H100, H200 (datacenter)
- **Any CUDA-capable GPU!** Even budget/mobile GPUs help!

**CPUs of interest:**
- Dual CPU servers (2× Xeon, 2× EPYC)
- High core count CPUs (16+ cores: Threadripper, EPYC, Xeon)
- Consumer CPUs (AMD Ryzen, Intel Core)
- **Any CPU!** From laptops to servers!

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
- Auto-detects GPU or CPU mode
- Collects system specs (GPU model, VRAM, CPU cores, etc.)
- Runs optimization (GPU mode includes auto-tuner)
- Saves results to timestamped JSON file

**What to report:**
- Just send the `benchmark_results_YYYYMMDD_HHMMSS.json` file!

---

### Option 2: Using the Launcher (Interactive)

```bash
python launcher.py
```

Split-screen display shows real-time performance and optimization.

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

**What to report:**
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
- Make sure CUDA drivers are installed
- Verify CuPy is installed correctly: `python -c "import cupy; print(cupy.cuda.runtime.getDeviceProperties(0))"`

**Auto-tuner crashes/hangs**
- This is actually useful data! Some configurations may not work on certain GPUs
- The auto-tuner has built-in failure detection and will skip bad configs
- Let me know which configurations caused issues

**"ModuleNotFoundError: No module named 'cupy'"**
- Install CuPy: `pip install cupy-cuda12x` (or cuda11x for older CUDA versions)

**Unicode/encoding errors (Windows only)**
- These should be fixed, but if you see any, let me know!

---

## Privacy & Safety

- The code only performs mathematical computations (Collatz Conjecture checking)
- No data is collected, uploaded, or shared
- All state is saved locally in JSON files
- Feel free to review the code before running - it's all open source
- Runs can be stopped at any time with Ctrl+C

---

## Why This Matters

The Collatz Conjecture is one of mathematics' most famous unsolved problems. While we're not expecting to find a counterexample (the conjecture has been verified to huge numbers already), this project is about:

1. **Pushing GPU optimization techniques** to their limits
2. **Exploring adaptive auto-tuning** for CUDA workloads
3. **Building efficient mathematical computing infrastructure**
4. **Having fun with big numbers!**

---

## Contributing Results

If you're able to run this, please comment with:

1. **GPU Model** (e.g., "RTX 4090 24GB")
2. **Peak odd/s rate** (from hybrid checker)
3. **Optimal config** (from auto-tuner, if it found one)
4. **Any interesting observations**

Even if you just run it for a few minutes, the data would be incredibly valuable!

---

Thanks for considering helping out! This has been a fun project and I'm excited to see how it performs on different hardware configurations.

**Edit:** If you have multiple GPUs or want to test different configurations, that's awesome too! The auto-tuner saves its state so you can stop/resume anytime.
