# Error Handling & Diagnostics Guide

## Overview

The Collatz Engine now includes comprehensive error handling to catch hardware issues, missing libraries, driver problems, and configuration errors.

## Quick Diagnostics

Run system diagnostics to check for issues:

```bash
python run_diagnostics.py
```

Or through the launcher:

```bash
python launcher.py --diagnostics
```

## Error Logging

All errors are automatically logged to `error_log.json` with full context including:
- Error type (hardware, library, driver, config, etc.)
- Timestamp
- System information
- Stack traces
- Error details

## Common Issues & Solutions

### GPU Not Available

**Symptoms:**
- "CuPy not installed" message
- "GPU initialization failed"

**Solutions:**
1. Install CuPy for your CUDA version:
   ```bash
   pip install cupy-cuda12x  # For CUDA 12.x
   pip install cupy-cuda11x  # For CUDA 11.x
   ```
2. Update GPU drivers
3. Use CPU mode instead: `python CollatzEngine.py cpu`

### Missing Libraries

**Symptoms:**
- ImportError messages
- "Missing required libraries" error

**Solutions:**
```bash
pip install numpy psutil
```

### Config File Corrupted

**Symptoms:**
- "Invalid JSON in config file"
- "Config validation failed"

**Solutions:**
- The engine automatically recovers by using defaults
- Check `error_log.json` for details
- Manually delete corrupted config files (they'll be recreated)

### CUDA Runtime Errors

**Symptoms:**
- "CUDA runtime error"
- "GPU hardware problems"

**Solutions:**
1. Update NVIDIA drivers
2. Check GPU temperature (may be thermal throttling)
3. Restart system to reset GPU state
4. Run diagnostics: `python run_diagnostics.py`

### File Permission Errors

**Symptoms:**
- "No write permission"
- "File access error"

**Solutions:**
1. Run as administrator (Windows) or with sudo (Linux)
2. Check folder permissions
3. Move to a folder with write access

## Error Log Structure

`error_log.json` contains:

```json
{
  "last_updated": "2025-10-23T...",
  "total_errors": 5,
  "errors": [
    {
      "timestamp": "2025-10-23T12:00:00",
      "type": "gpu_initialization",
      "message": "GPU detected but initialization failed",
      "system": {
        "platform": "Windows-10-...",
        "python_version": "3.13.0",
        "processor": "Intel64 Family..."
      },
      "exception": {
        "type": "CUDARuntimeError",
        "message": "cudaErrorMemoryAllocation",
        "traceback": "..."
      }
    }
  ]
}
```

## Diagnostic Report

`diagnostic_report.json` is created when you run diagnostics:

```json
{
  "timestamp": "2025-10-23T...",
  "system": {...},
  "checks": {
    "libraries": {"status": "OK"},
    "gpu": {
      "status": "OK",
      "details": {
        "gpu_name": "NVIDIA RTX 4090",
        "vram_total_gb": 24.0,
        "compute_capability": "8.9"
      }
    },
    "permissions": {"status": "OK"},
    "configs": {...}
  },
  "overall_status": "PASSED"
}
```

## Automatic Error Recovery

The engine automatically handles:

1. **Invalid Config Files**: Falls back to defaults
2. **GPU Failures**: Switches to CPU mode
3. **Missing Tuning Files**: Creates default configurations
4. **Permission Issues**: Logs error and continues where possible

## Manual Intervention Required

Some errors require manual fixes:

- **Driver issues**: Update GPU drivers
- **Missing libraries**: Install via pip
- **Hardware failures**: Check GPU health
- **Disk full**: Free up space

## Getting Help

When reporting issues, include:

1. Output from `python run_diagnostics.py`
2. Relevant entries from `error_log.json`
3. System specifications (auto-included in error logs)
4. Steps to reproduce the error

## Maintenance

Error logs are automatically:
- Limited to last 100 errors
- Can be cleared with `error_handler.clear_old_errors(days=30)`
- Saved in JSON format for easy parsing

Old errors can be manually cleared by deleting `error_log.json` (it will be recreated on next error).
