# Quick Start Guide

## For First-Time Users

### 1. Check System Requirements

**GPU Mode (Recommended):**
```bash
python run_diagnostics.py
```

This checks:
- ✓ Python libraries
- ✓ GPU availability (detects all GPUs)
- ✓ CUDA drivers
- ✓ File permissions

**Multi-GPU Systems:**
- Automatically detected and utilized
- Workload distributed across all GPUs
- Heterogeneous configurations supported

**CPU Mode (Fallback):**
- Just Python 3.8+ required
- No GPU needed

### 2. Install Dependencies

**For GPU Mode:**
```bash
pip install cupy-cuda12x  # or cupy-cuda11x for older CUDA
```

**For CPU Mode:**
```bash
# No extra dependencies needed!
```

### 3. Run the Launcher

```bash
python launcher.py
```

**What happens:**
- System checks if optimization is needed
- **First run:** Auto-tuner starts automatically (GPU mode, ~20-30 minutes)
- **Subsequent runs:** Skips optimization if hardware unchanged
- Split-screen shows engine + tuner (GPU mode) or just engine (CPU mode)

**Can I stop it?**
- Press Ctrl+C anytime
- Auto-tuner resumes from saved state next time
- Engine saves progress every 500 billion numbers

### 4. Run a Benchmark (Optional)

After optimization completes:

```bash
python benchmark.py
```

This creates a timestamped JSON file with your system's performance data.

---

## Common Workflows

### Just Want to Run It
```bash
python launcher.py
```
That's it! The launcher handles everything automatically.

### Want Peak Performance
```bash
# 1. Optimize system
python launcher.py
# (Wait for auto-tuner to complete - GPU mode only)

# 2. Run benchmark
python benchmark.py
```

### CPU-Only Mode (No GPU)
```bash
python CollatzEngine.py cpu
```
No optimization needed for CPU mode.

### Check for Problems
```bash
python run_diagnostics.py
```
or
```bash
python launcher.py --diagnostics
```

### Resume Interrupted Optimization
```bash
python launcher.py
```
It automatically detects incomplete optimization and resumes.

---

## Understanding the Output

### Launcher Output (GPU Mode)

```
System Status Check:
  Status: Optimized / Not Optimized / First Run
  Reason: Hardware unchanged / Hardware changed / Never optimized

[ENGINE] Started (PID: 12345)
[TUNER] Started (PID: 12346)  # Only if optimization needed
```

**Split Screen:**
- **Top half:** Collatz Engine (real-time verification)
- **Bottom half:** Auto-Tuner (optimization progress)

### Engine Metrics

```
Total tested: 572,345,678,901,234
Current rate: 9,876,543,210 odd/s
Highest proven: 572,345,678,901,234
```

- **odd/s:** Raw numbers checked per second
- **Highest proven:** Largest number verified to reach 1

### Auto-Tuner Progress

```
[STAGE 1] Binary Search... 
[NEW PEAK] 8,500,000,000 odd/s
[STAGE 2] Fine-tuning...
[STAGE 3] Progressive refinement...
```

Stages take ~20-30 minutes total (GPU mode only).

---

## First Run Timeline

### GPU Mode
1. **Minute 0-1:** System checks, engine starts
2. **Minute 1-2:** Auto-tuner startup (if needed)
3. **Minute 2-15:** Stage 1 binary search
4. **Minute 15-25:** Stage 2 fine-tuning  
5. **Minute 25-30:** Stage 3 refinement
6. **Done:** System optimized, runs at peak performance

### CPU Mode
1. **Minute 0-1:** System checks, engine starts
2. **Done:** No optimization needed, runs immediately

---

## Troubleshooting Quick Fixes

### "CuPy not found"
```bash
pip install cupy-cuda12x
```
or use CPU mode: `python CollatzEngine.py cpu`

### "GPU initialization failed"
1. Update GPU drivers
2. Check CUDA installation
3. Run: `python run_diagnostics.py`
4. Or fallback to CPU mode

### "Permission denied"
- Windows: Run as administrator
- Linux: Check folder permissions or use sudo

### Config file errors
- Engine auto-recovers with defaults
- Check `error_log.json` for details
- Delete corrupted files (they'll be recreated)

### Auto-tuner stuck/crashed
- Press Ctrl+C
- Run `python launcher.py` again
- It auto-resumes from saved state

---

## What Files Get Created?

**During normal operation:**
- `collatz_config.json` - Progress state
- `gpu_tuning.json` - Optimal settings (GPU mode)
- `optimization_state.json` - Optimization status
- `error_log.json` - Error history (if any errors occur)

**When you run diagnostics:**
- `diagnostic_report.json` - System health check

**When you run benchmark:**
- `benchmark_results_YYYYMMDD_HHMMSS.json` - Performance data

**All these files:**
- Stay on your computer (not uploaded anywhere)
- Can be safely deleted (they'll be recreated)
- Are in `.gitignore` (won't be committed to git)

---

## Advanced Usage

### Force Fresh Optimization
```bash
# Delete optimization state
del optimization_state.json     # Windows
rm optimization_state.json      # Linux/Mac

# Run launcher (will re-optimize)
python launcher.py
```

### Run Without Launcher
```bash
# Engine only (no auto-tuner)
python CollatzEngine.py

# Auto-tuner only
python auto_tuner.py
```

### Check Optimization Status
Open `optimization_state.json` to see:
- Hardware fingerprint
- Optimization completion status
- Last update timestamp

---

## Getting Help

1. **Check error log:** `error_log.json`
2. **Run diagnostics:** `python run_diagnostics.py`
3. **Read troubleshooting:** `ERROR_HANDLING.md`
4. **Check documentation:** `README.md`
5. **Open an issue:** Include diagnostic report and error log

---

## Next Steps

Once you're running:
- Let it run! Verification continues indefinitely
- Check back for new peak rates
- Run benchmarks to compare configurations
- Share results (see `CONTRIBUTING.md`)
- Try different hardware if available

**Most important:** Have fun exploring the Collatz Conjecture! 🚀
