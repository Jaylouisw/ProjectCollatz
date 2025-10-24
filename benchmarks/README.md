# Community Benchmark Results

This directory contains benchmark results submitted by the community from various GPU and CPU configurations.

## How to Submit Your Benchmark

1. **Optimize your system first (recommended):**
   ```bash
   python launcher.py
   ```
   Let the auto-tuner complete (GPU mode only) for best results.

2. **Run the benchmark script:**
   ```bash
   python benchmark.py
   ```
   This will generate a file named `benchmark_results_YYYYMMDD_HHMMSS.json`

3. **Check the results:**
   - The file will show if your system was optimized or not
   - For best performance data, ensure `"system_optimized": true`

4. **Submit:**
   - Fork this repository
   - Add your benchmark file to the `benchmarks/` directory
   - Submit a pull request with **ONLY** the benchmark file (no other changes)

## Naming Convention

Please rename your file to include your hardware:

**GPU Mode:**
```
benchmark_<GPU_MODEL>_<DATE>.json
```

**CPU Mode:**
```
benchmark_<CPU_MODEL>_<CORES>core_<DATE>.json
```

Examples:
```
benchmark_RTX4090_20251023.json
benchmark_RTX3060_20251023_run2.json
benchmark_EPYC7763_128core_20251023.json
benchmark_Ryzen9_16core_20251023.json
```

## File Requirements

- Only `benchmark_results_*.json` or `benchmark_*.json` files in the `benchmarks/` directory
- No modifications to any other files
- Maximum file size: 1MB
- Must be valid JSON format

## Privacy

Benchmark files contain:
- Hardware specifications (GPU/CPU model, specs)
- Performance metrics (odd/s, configuration)
- System platform info
- Mode (GPU hybrid or CPU-only)
- Optimization status
- **NO personal information**
- Machine IDs are hashed

You can review your benchmark file before submitting to ensure you're comfortable with the data being shared.

## What Happens to Submitted Benchmarks

- Results are aggregated to understand performance across different hardware
- May be featured in project documentation
- Helps optimize the auto-tuner for various GPU/CPU architectures
- Contributors may be acknowledged in the project README
- Helps identify common hardware issues or optimal configurations

Thank you for contributing to the Collatz Engine project!
