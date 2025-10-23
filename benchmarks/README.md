# Community Benchmark Results

This directory contains benchmark results submitted by the community from various GPU configurations.

## How to Submit Your Benchmark

1. Run the benchmark script: `python benchmark.py`
2. This will generate a file named `benchmark_results_YYYYMMDD_HHMMSS.json`
3. Fork this repository
4. Add your benchmark file to the `benchmarks/` directory
5. Submit a pull request with **ONLY** the benchmark file (no other changes)

## Naming Convention

Please rename your file to include your GPU model:
```
benchmark_<GPU_MODEL>_<DATE>.json
```

Example:
```
benchmark_RTX4090_20251023.json
benchmark_RTX3060_20251023_run2.json
```

## File Requirements

- Only `benchmark_results_*.json` or `benchmark_*.json` files in the `benchmarks/` directory
- No modifications to any other files
- Maximum file size: 1MB
- Must be valid JSON format

## Privacy

Benchmark files contain:
- GPU specifications
- Performance metrics
- System platform info
- **NO personal information**
- Machine IDs are hashed

You can review your benchmark file before submitting to ensure you're comfortable with the data being shared.

## What Happens to Submitted Benchmarks

- Results are aggregated to understand performance across different hardware
- May be featured in project documentation
- Helps optimize the auto-tuner for various GPU architectures
- Contributors may be acknowledged in the project README

Thank you for contributing to the Collatz Engine project!
