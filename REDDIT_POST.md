# Looking for High-End GPU Volunteers to Benchmark Collatz Conjecture Engine

**TL;DR:** I've built a highly optimized CUDA-based Collatz Conjecture checker with adaptive auto-tuning. Looking for volunteers with high-end GPUs (4090, H100, H200, etc.) to help benchmark performance across different hardware.

---

## About the Project

I've been working on an optimized GPU implementation for exploring the Collatz Conjecture. The engine uses:

- **Hybrid CPU+GPU architecture** with CuPy for maximum throughput
- **Adaptive auto-tuner** that dynamically optimizes GPU parameters (batch size, thread count, work multipliers, blocks per SM)
- **Efficient odd-only checking** (skips even numbers since they're trivial)
- **Persistent state** with resume capability and checkpoint system
- **Real-time performance monitoring** with split-screen display

On my GPU (6GB VRAM), I'm currently hitting **~10 billion odd/s** (20 billion effective/s when counting skipped evens). The code is heavily optimized and should scale well to more powerful hardware.

---

## What I'm Looking For

I'm curious how this performs across different GPU architectures! **Any CUDA-capable GPU** is welcome - from budget cards to data center hardware. Every benchmark helps!

**Especially interested in:**
- **RTX 4090** (24GB VRAM)
- **RTX 4080/4070** (12-16GB VRAM)  
- **RTX 3090/3080** (10-24GB VRAM)
- **A100** (40GB/80GB VRAM)
- **H100/H200** (80GB+ VRAM)
- **Any GTX/RTX/Tesla/Quadro GPU with CUDA support**

**But honestly, any CUDA GPU data is valuable!** Even if you have an older GTX 1060, GTX 1660, RTX 2060, or mobile GPU - your results would still help me understand:

1. How well the auto-tuner adapts to different GPU architectures and memory configurations
2. Performance scaling from budget to flagship hardware
3. What the theoretical upper limits are for this approach
4. Whether there are any architecture-specific bottlenecks I haven't discovered yet

**Don't hesitate to contribute even if your GPU seems "too old" or "not powerful enough"** - diverse data points across the entire CUDA ecosystem are incredibly valuable for optimization!

---

## What You'll Need

- **CUDA-capable GPU** with recent drivers
- **Python 3.8+** 
- **CuPy** (CUDA acceleration library)
- **~5-10 minutes** of runtime to get stable numbers

---

## Installation & Running Instructions

### Quick Setup

```bash
# Clone or download the repository
cd CollatzEngine

# Install dependencies
pip install cupy-cuda12x  # or cupy-cuda11x depending on your CUDA version
```

### Option 1: Automated Benchmark (Easiest!)

For the simplest experience with automatic results collection:

```bash
python benchmark.py
```

**What it does:**
- Automatically collects all your system specifications (GPU model, VRAM, compute capability, etc.)
- Runs both the hybrid checker and auto-tuner together
- Monitors performance and collects all metrics
- Saves everything to a timestamped JSON file you can send back
- You choose how long to run (default: 10 minutes)

**What to report:**
- Just send back the generated `benchmark_results_YYYYMMDD_HHMMSS.json` file!
- Everything I need is automatically captured

This is the recommended option if you just want to help benchmark without diving into details.

---

---

### Option 2: Using the Launcher (Interactive)

The launcher automatically manages both the hybrid checker and auto-tuner with a clean split-screen display:

```bash
python launcher.py
```

**What to expect:**
- The hybrid checker starts first and runs for 60 seconds to establish baseline performance
- The auto-tuner then starts and begins optimizing GPU parameters
- You'll see real-time output split into two sections:
  - **Top section:** Hybrid checker progress (numbers tested, current rate, highest proven value)
  - **Bottom section:** Auto-tuner status (current configuration being tested, optimization progress)
- Let it run for **5-10 minutes** to get through Stage 1 optimization
- Press **Ctrl+C** to stop both processes cleanly

**What to report:**
- Your GPU model and VRAM
- The "Current rate" from the hybrid checker (look for the highest stable odd/s value)
- Any configurations the auto-tuner reports as "[NEW PEAK]"
- Screenshot or copy/paste of final output would be amazing!

---

### Option 3: Running Scripts Separately (Advanced)

If you prefer more control or the launcher doesn't work on your system:

**Terminal 1 - Hybrid Checker:**
```bash
python collatz_hybrid.py
```

**Terminal 2 - Auto-Tuner (wait 60 seconds after starting Terminal 1):**
```bash
python auto_tuner.py
```

**What to expect:**
- Terminal 1 shows the main checking progress with session summaries every second
- Terminal 2 runs optimization cycles, testing different GPU configurations
- Let both run for **5-10 minutes** minimum
- Press **Ctrl+C** in each terminal to stop (stop auto-tuner first, then hybrid checker)

**What to report:**
- Your GPU model and VRAM
- Final "Current rate" from Terminal 1 (odd/s)
- Best configuration from Terminal 2 (batch size, threads, work multiplier, blocks per SM)
- Any interesting observations (crashes, performance anomalies, etc.)

---

## What the Numbers Mean

- **odd/s:** Odd numbers checked per second (this is the raw GPU throughput)
- **effective/s:** Total numbers conceptually checked per second (odd/s × 2, since even numbers are trivial)
- **Session tested:** Total numbers checked this run
- **Total tested:** Cumulative across all runs (uses persistent state)
- **Highest proven:** Largest starting value verified to reach 1

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
