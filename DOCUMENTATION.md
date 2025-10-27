# Documentation Index

Complete guide to all Collatz Engine documentation.

## Getting Started

📘 **[QUICK_START.md](QUICK_START.md)** - Start here!
- First-time setup
- Common workflows  
- Troubleshooting quick fixes
- Understanding output
- Timeline expectations

📗 **[README.md](README.md)** - Project overview
- Features and performance
- Installation instructions
- Usage options (launcher, direct, benchmark)
- How it works (architecture)
- Configuration files
- **Technical Optimizations** - Applied and avoided optimizations with justifications

## Technical Documentation

⚙️ **[KERNEL_OPTIMIZATION_NOTES.md](KERNEL_OPTIMIZATION_NOTES.md)** - Deep dive into optimizations
- GPU kernel improvements (branchless operations)
- Why SIMD doesn't work for Collatz
- Why Tensor Cores aren't applicable
- Reddit community feedback analysis
- Performance benchmarks and trade-offs

🔬 **[simd_collatz.py](simd_collatz.py)** - SIMD investigation proof-of-concept
- NumPy vectorization attempt
- Why it's 2x slower than scalar
- Benchmark results
- Lessons learned

## Troubleshooting & Support

🔧 **[ERROR_HANDLING.md](ERROR_HANDLING.md)** - Complete troubleshooting guide
- Common issues and solutions
- Error log structure
- Diagnostic reports
- Recovery procedures
- Getting help

🩺 **Run Diagnostics:**
```bash
python run_diagnostics.py
python launcher.py --diagnostics
```

## Contributing

🤝 **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
- Benchmark submissions (easy!)
- Code contributions (advanced)
- Guidelines and requirements
- What we're looking for

📊 **[benchmarks/README.md](benchmarks/README.md)** - Benchmark submission guide
- How to submit
- Naming conventions
- Privacy information
- What happens to data

## Community & Outreach

📢 **[REDDIT_POST.md](REDDIT_POST.md)** - Volunteer recruitment post
- Project description
- Hardware of interest
- Installation instructions
- Troubleshooting tips
- How to share results

## Technical Reference

### Main Scripts

- **`CollatzEngine.py`** - Main verification engine
  - Multi-GPU mode (automatically detects all GPUs)
  - GPU hybrid mode (CUDA + CPU workers)
  - CPU-only mode (pure multiprocessing)
  - Command-line: `python CollatzEngine.py [gpu|cpu]`

- **`auto_tuner.py`** - GPU optimization (GPU mode only)
  - Multi-GPU support (heterogeneous configurations)
  - Stage 1: Binary search
  - Stage 2: Fine-tuning
  - Stage 3: Progressive refinement
  - Auto-resume on interrupt
  - Command-line: `python auto_tuner.py [--auto-resume]`

- **`launcher.py`** - Unified launcher
  - Intelligent optimization management
  - Split-screen display
  - Pre-flight system checks
  - Command-line: `python launcher.py [--diagnostics]`

- **`benchmark.py`** - Performance testing
  - Auto-detects mode (GPU/CPU)
  - Collects system specs
  - Records optimization status
  - Command-line: `python benchmark.py`

- **`run_diagnostics.py`** - System health check
  - Hardware verification
  - Library checks
  - Permission validation
  - Config file validation
  - Command-line: `python run_diagnostics.py`

### Support Modules

- **`optimization_state.py`** - Optimization state management
  - Hardware fingerprinting (SHA256)
  - Completion tracking
  - Hardware change detection
  - Benchmark status

- **`error_handler.py`** - Error handling & logging
  - Centralized error logger
  - System diagnostics
  - Hardware checks
  - Config validation
  - Safe CuPy import

- **`contribution_tracker.py`** - Contribution tracking
  - User profiles
  - Leaderboards
  - Export/merge functionality
  - Privacy-preserving hashing

### Configuration Files

All auto-generated and in `.gitignore`:

- **`collatz_config.json`** - Main engine state
  - Progress tracking
  - Highest proven number
  - Total tested count
  - Runtime statistics

- **`gpu_tuning.json`** - GPU optimization settings
  - Batch size
  - Threads per block
  - Work multiplier
  - Blocks per SM
  - CPU worker count

- **`autotuner_state.json`** - Auto-tuner resume state
  - Current stage
  - Best configuration
  - Best rate achieved
  - Iteration count
  - Timestamp

- **`optimization_state.json`** - Optimization status
  - Hardware fingerprint
  - Optimization completed flag
  - Benchmark completed flag
  - Last update timestamp

- **`error_log.json`** - Error history
  - Last 100 errors
  - Full stack traces
  - System information
  - Error categorization

- **`diagnostic_report.json`** - System health report
  - Library status
  - GPU availability
  - Permission checks
  - Config validation
  - Overall status

- **`user_profile.json`** - Contribution profile (optional)
  - Username
  - Machine ID (hashed)
  - Total contributions
  - Verification ranges

## Quick Reference

### First Run
```bash
python launcher.py
```
System optimizes automatically on first run (GPU mode).

### Subsequent Runs
```bash
python launcher.py
```
Skips optimization if hardware unchanged.

### CPU-Only Mode
```bash
python CollatzEngine.py cpu
```
No optimization needed.

### Benchmark
```bash
python benchmark.py
```
Run after optimization for best results.

### Diagnostics
```bash
python run_diagnostics.py
```
Check system health anytime.

### Force Re-Optimization
```bash
# Delete state file
del optimization_state.json  # Windows
rm optimization_state.json   # Linux/Mac

# Run launcher
python launcher.py
```

## File Structure

```
CollatzEngine/
├── README.md                    # Project overview
├── QUICK_START.md              # First-time user guide
├── ERROR_HANDLING.md           # Troubleshooting guide
├── CONTRIBUTING.md             # Contribution guidelines
├── REDDIT_POST.md              # Community post template
├── LICENSE                      # CC BY-NC-SA 4.0
│
├── CollatzEngine.py            # Main engine
├── auto_tuner.py               # GPU optimizer
├── launcher.py                 # Unified launcher
├── benchmark.py                # Performance testing
├── run_diagnostics.py          # System check
│
├── optimization_state.py       # State management
├── error_handler.py            # Error handling
├── contribution_tracker.py     # Contribution system
│
├── collatz_config.json         # (auto-generated)
├── gpu_tuning.json             # (auto-generated)
├── autotuner_state.json        # (auto-generated)
├── optimization_state.json     # (auto-generated)
├── error_log.json              # (auto-generated)
├── diagnostic_report.json      # (auto-generated)
│
└── benchmarks/
    ├── README.md               # Benchmark guide
    └── (community submissions)
```

## Getting Help

1. **Quick fixes:** [QUICK_START.md](QUICK_START.md#troubleshooting-quick-fixes)
2. **Detailed troubleshooting:** [ERROR_HANDLING.md](ERROR_HANDLING.md)
3. **System diagnostics:** `python run_diagnostics.py`
4. **Error history:** Check `error_log.json`
5. **GitHub issues:** Include diagnostic report

## What to Read

**Just want to run it:**
→ [QUICK_START.md](QUICK_START.md)

**Want to understand how it works:**
→ [README.md](README.md)

**Having problems:**
→ [ERROR_HANDLING.md](ERROR_HANDLING.md)

**Want to contribute:**
→ [CONTRIBUTING.md](CONTRIBUTING.md)

**Want to share with others:**
→ [REDDIT_POST.md](REDDIT_POST.md)

---

**Most important:** Start with [QUICK_START.md](QUICK_START.md) if you're new! 🚀
