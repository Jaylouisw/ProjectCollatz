"""
Collatz Engine Benchmark Script
Automatically collects system specs, runs optimization, and saves results
Supports both GPU hybrid mode and CPU-only mode

Copyright (c) 2025 Jay Wenden (CollatzEngine)
Licensed under CC BY-NC-SA 4.0
https://creativecommons.org/licenses/by-nc-sa/4.0/
"""

import subprocess
import time
import json
import platform
import sys
from datetime import datetime
import os
import optimization_state

# Import error handler
try:
    from error_handler import logger, check_gpu_availability
    ERROR_HANDLING = True
except ImportError:
    ERROR_HANDLING = False
    logger = None

try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

def get_system_specs():
    """Collect system specifications."""
    specs = {
        "timestamp": datetime.now().isoformat(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu": platform.processor(),
        "cpu_count": os.cpu_count(),
    }
    
    # GPU info - detect all GPUs
    if GPU_AVAILABLE:
        try:
            gpu_count = cp.cuda.runtime.getDeviceCount()
            specs["gpu_count"] = gpu_count
            specs["gpus"] = []
            
            for i in range(gpu_count):
                with cp.cuda.Device(i):
                    props = cp.cuda.runtime.getDeviceProperties(i)
                    mem_info = cp.cuda.Device(i).mem_info
                    
                    gpu_info = {
                        "id": i,
                        "name": props['name'].decode() if isinstance(props['name'], bytes) else props['name'],
                        "vram_total_gb": round(mem_info[1] / (1024**3), 2),
                        "vram_free_gb": round(mem_info[0] / (1024**3), 2),
                        "compute_capability": f"{props['major']}.{props['minor']}",
                        "multiprocessor_count": props['multiProcessorCount'],
                        "clock_rate_mhz": props['clockRate'] / 1000,
                        "memory_clock_rate_mhz": props['memoryClockRate'] / 1000,
                        "memory_bus_width": props['memoryBusWidth'],
                        "max_threads_per_block": props['maxThreadsPerBlock'],
                        "max_threads_per_multiprocessor": props['maxThreadsPerMultiProcessor'],
                    }
                    specs["gpus"].append(gpu_info)
            
            # Keep backward compatibility with single GPU field (primary GPU)
            if gpu_count > 0:
                specs["gpu"] = specs["gpus"][0]
        except Exception as e:
            specs["gpu_count"] = 0
            specs["gpus"] = []
            specs["gpu"] = {"error": str(e)}
    else:
        specs["gpu_count"] = 0
        specs["gpus"] = []
        specs["gpu"] = {"error": "GPU not available"}
    
    return specs

def parse_checker_output(line):
    """Parse hybrid checker output for metrics."""
    data = {}
    if "Current rate:" in line:
        try:
            parts = line.split("Current rate:")[1].split("odd/s")[0].strip()
            data["current_rate_odd_per_sec"] = float(parts.replace(",", ""))
        except:
            pass
    
    if "Highest proven:" in line:
        try:
            parts = line.split("Highest proven:")[1].split()[0].strip()
            data["highest_proven"] = parts
        except:
            pass
    
    if "Session tested:" in line:
        try:
            parts = line.split("Session tested:")[1].split()[0].strip()
            data["session_tested"] = parts
        except:
            pass
    
    if "Total tested:" in line:
        try:
            parts = line.split("Total tested:")[1].split()[0].strip()
            data["total_tested"] = parts
        except:
            pass
    
    if "Average rate:" in line:
        try:
            parts = line.split("Average rate:")[1].split("odd/s")[0].strip()
            data["average_rate_odd_per_sec"] = float(parts.replace(",", ""))
        except:
            pass
    
    return data

def parse_tuner_output(line):
    """Parse auto-tuner output for configs and rates."""
    data = {}
    
    if "[NEW PEAK]" in line or "[NEW BEST]" in line:
        try:
            parts = line.split("odd/s")[0]
            rate = parts.split()[-1]
            data["new_peak_rate"] = float(rate.replace(",", ""))
        except:
            pass
    
    if "Batch:" in line and "Threads:" in line:
        try:
            config = {}
            if "Batch:" in line:
                batch = line.split("Batch:")[1].split("|")[0].strip()
                config["batch_size"] = int(batch.replace(",", ""))
            if "Threads:" in line:
                threads = line.split("Threads:")[1].split("|")[0].strip()
                config["threads"] = int(threads)
            if "Work:" in line:
                work = line.split("Work:")[1].split("|")[0].strip()
                config["work_multiplier"] = int(work)
            if "Blocks/SM:" in line:
                blocks = line.split("Blocks/SM:")[1].strip()
                config["blocks_per_sm"] = int(blocks)
            if config:
                data["config"] = config
        except:
            pass
    
    if "STAGE 1 COMPLETE" in line:
        data["stage_1_complete"] = True
        try:
            parts = line.split("Best rate:")[1].split("odd/s")[0].strip()
            data["stage_1_best_rate"] = float(parts.replace(",", ""))
        except:
            pass
    
    return data

def run_benchmark(duration_minutes=10):
    """Run the benchmark for specified duration."""
    print("=" * 70)
    print("COLLATZ ENGINE BENCHMARK")
    print("=" * 70)
    print(f"Duration: {duration_minutes} minutes")
    print("Collecting system specifications...")
    print()
    
    # Check optimization status
    opt_status = optimization_state.get_optimization_status()
    is_optimized = optimization_state.is_system_optimized()
    
    if is_optimized:
        print("✓ System is optimized for current hardware")
    else:
        print(f"⚠ Warning: System not optimized - {opt_status['reason']}")
        print("  Benchmark results may not reflect peak performance.")
        print("  Run launcher.py to optimize before benchmarking.")
    print()
    
    # Determine mode and detect all GPUs
    mode = 'cpu'
    if GPU_AVAILABLE:
        try:
            gpu_count = cp.cuda.runtime.getDeviceCount()
            mode = 'gpu'
            if gpu_count > 1:
                print(f"Mode: GPU Hybrid (detected {gpu_count} GPUs - Multi-GPU)")
                for i in range(gpu_count):
                    with cp.cuda.Device(i):
                        props = cp.cuda.runtime.getDeviceProperties(i)
                        print(f"  [{i}] {props['name'].decode()}")
            else:
                device = cp.cuda.Device()
                props = cp.cuda.runtime.getDeviceProperties(device.id)
                print(f"Mode: GPU Hybrid (detected {props['name'].decode()})")
        except:
            print("Mode: CPU-only (GPU detected but initialization failed)")
    else:
        print("Mode: CPU-only (no GPU available)")
    print()
    
    specs = get_system_specs()
    
    print("System Specifications:")
    print(f"  Platform: {specs['platform']}")
    print(f"  Python: {specs['python_version']}")
    print(f"  CPU: {specs['cpu']}")
    print(f"  CPU Cores: {specs['cpu_count']}")
    if 'gpu' in specs and 'name' in specs['gpu']:
        print(f"  GPU: {specs['gpu']['name']}")
        print(f"  VRAM: {specs['gpu']['vram_total_gb']} GB")
        print(f"  Compute: {specs['gpu']['compute_capability']}")
        print(f"  SMs: {specs['gpu']['multiprocessor_count']}")
    print()
    
    print("Starting benchmark processes...")
    print("=" * 70)
    print()
    
    # Start CollatzEngine with appropriate mode
    engine_cmd = [sys.executable, "CollatzEngine.py"]
    if mode == 'cpu':
        engine_cmd.append('cpu')
    else:
        engine_cmd.append('gpu')
    
    checker_process = subprocess.Popen(
        engine_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    print(f"[ENGINE] Started CollatzEngine in {mode.upper()} mode")
    
    # Wait 60 seconds before starting auto-tuner (GPU mode only)
    tuner_process = None
    if mode == 'gpu':
        print("[WAITING] Waiting 60 seconds for baseline performance...")
        time.sleep(60)
        
        # Start auto-tuner
        tuner_process = subprocess.Popen(
            [sys.executable, "auto_tuner.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            stdin=subprocess.PIPE
        )
        
        # Auto-respond to resume prompt if it appears
        try:
            tuner_process.stdin.write('n\n')
            tuner_process.stdin.flush()
        except:
            pass
        
        print("[TUNER] Started auto-tuner")
    else:
        print("[CPU MODE] Skipping auto-tuner (GPU-only feature)")
    print()
    
    print(f"[RUNNING] Benchmark will run for {duration_minutes} minutes...")
    print("[INFO] You'll see periodic updates below")
    print("=" * 70)
    print()
    
    # Collect data
    results = {
        "mode": mode,
        "system_specs": specs,
        "benchmark_duration_minutes": duration_minutes,
        "checker_metrics": {},
        "peak_rate_odd_per_sec": 0,  # Track peak rate
        "tuner_configs": [] if mode == 'gpu' else None,
        "tuner_peaks": [] if mode == 'gpu' else None,
        "raw_output": {
            "checker": [],
            "tuner": [] if mode == 'gpu' else None
        }
    }
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    last_update = time.time()
    update_interval = 30  # Update every 30 seconds
    
    try:
        while time.time() < end_time:
            # Check if processes are still running
            if checker_process.poll() is not None:
                print("\n[ERROR] Hybrid checker process died unexpectedly!")
                break
            
            if tuner_process.poll() is not None:
                print("\n[WARNING] Auto-tuner process ended")
            
            # Read from checker (non-blocking)
            try:
                import select
                if sys.platform != 'win32':
                    # Unix-like systems
                    ready, _, _ = select.select([checker_process.stdout], [], [], 0.1)
                    if ready:
                        line = checker_process.stdout.readline()
                        if line:
                            line = line.strip()
                            results["raw_output"]["checker"].append(line)
                            parsed = parse_checker_output(line)
                            if parsed:
                                results["checker_metrics"].update(parsed)
                else:
                    # Windows - just try to read
                    line = checker_process.stdout.readline()
                    if line:
                        line = line.strip()
                        results["raw_output"]["checker"].append(line)
                        parsed = parse_checker_output(line)
                        if parsed:
                            results["checker_metrics"].update(parsed)
                            # Track peak rate
                            if "current_rate_odd_per_sec" in parsed:
                                if parsed["current_rate_odd_per_sec"] > results["peak_rate_odd_per_sec"]:
                                    results["peak_rate_odd_per_sec"] = parsed["current_rate_odd_per_sec"]
            except:
                pass
            
            # Read from tuner (non-blocking) - GPU mode only
            if tuner_process:
                try:
                    if sys.platform != 'win32':
                        ready, _, _ = select.select([tuner_process.stdout], [], [], 0.1)
                        if ready:
                            line = tuner_process.stdout.readline()
                            if line:
                                line = line.strip()
                                results["raw_output"]["tuner"].append(line)
                                parsed = parse_tuner_output(line)
                                if "config" in parsed:
                                    results["tuner_configs"].append(parsed["config"])
                                if "new_peak_rate" in parsed:
                                    results["tuner_peaks"].append({
                                        "rate": parsed["new_peak_rate"],
                                        "timestamp": time.time() - start_time
                                    })
                                    print(f"[PEAK] New peak: {parsed['new_peak_rate']:,.0f} odd/s")
                                if parsed.get("stage_1_complete"):
                                    print(f"[STAGE 1] Complete! Best: {parsed.get('stage_1_best_rate', 'N/A'):,.0f} odd/s")
                    else:
                        line = tuner_process.stdout.readline()
                        if line:
                            line = line.strip()
                            results["raw_output"]["tuner"].append(line)
                            parsed = parse_tuner_output(line)
                            if "config" in parsed:
                                results["tuner_configs"].append(parsed["config"])
                            if "new_peak_rate" in parsed:
                                results["tuner_peaks"].append({
                                    "rate": parsed["new_peak_rate"],
                                    "timestamp": time.time() - start_time
                                })
                                print(f"[PEAK] New peak: {parsed['new_peak_rate']:,.0f} odd/s")
                            if parsed.get("stage_1_complete"):
                                print(f"[STAGE 1] Complete! Best: {parsed.get('stage_1_best_rate', 'N/A'):,.0f} odd/s")
                except:
                    pass
            
            # Periodic status update
            if time.time() - last_update > update_interval:
                elapsed = time.time() - start_time
                remaining = end_time - time.time()
                if "current_rate_odd_per_sec" in results["checker_metrics"]:
                    rate = results["checker_metrics"]["current_rate_odd_per_sec"]
                    print(f"[{elapsed/60:.1f}m] Current rate: {rate:,.0f} odd/s | {remaining/60:.1f}m remaining")
                else:
                    print(f"[{elapsed/60:.1f}m] Benchmark running... | {remaining/60:.1f}m remaining")
                last_update = time.time()
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n\n[STOPPED] Benchmark interrupted by user")
    
    finally:
        print("\n" + "=" * 70)
        print("STOPPING PROCESSES...")
        print("=" * 70)
        
        # Stop processes
        if tuner_process:
            try:
                tuner_process.terminate()
                time.sleep(2)
                if tuner_process.poll() is None:
                    tuner_process.kill()
            except:
                pass
        
        try:
            checker_process.terminate()
            time.sleep(2)
            if checker_process.poll() is None:
                checker_process.kill()
        except:
            pass
        
        print("[STOPPED] All processes terminated")
        print()
    
    # Calculate summary
    is_optimized = optimization_state.is_system_optimized()
    results["summary"] = {
        "benchmark_completed": True,
        "actual_duration_seconds": time.time() - start_time,
        "system_optimized": is_optimized,
        "mode": mode
    }
    
    if not is_optimized:
        results["summary"]["optimization_note"] = "System was not optimized when benchmark ran - results may not reflect peak performance"
    
    # Use the tracked peak rate instead of last seen rate
    if results["peak_rate_odd_per_sec"] > 0:
        results["summary"]["peak_checker_rate_odd_per_sec"] = results["peak_rate_odd_per_sec"]
        results["summary"]["peak_checker_rate_effective_per_sec"] = results["peak_rate_odd_per_sec"] * 2
    elif "current_rate_odd_per_sec" in results["checker_metrics"]:
        # Fallback to last rate if peak wasn't tracked
        results["summary"]["peak_checker_rate_odd_per_sec"] = results["checker_metrics"]["current_rate_odd_per_sec"]
        results["summary"]["peak_checker_rate_effective_per_sec"] = results["checker_metrics"]["current_rate_odd_per_sec"] * 2
    
    if results["tuner_peaks"] and len(results["tuner_peaks"]) > 0:
        max_peak = max(results["tuner_peaks"], key=lambda x: x["rate"])
        results["summary"]["peak_tuner_rate_odd_per_sec"] = max_peak["rate"]
        results["summary"]["peak_tuner_rate_effective_per_sec"] = max_peak["rate"] * 2
    
    if results["tuner_configs"] and len(results["tuner_configs"]) > 0:
        results["summary"]["optimal_config"] = results["tuner_configs"][-1]
    
    return results

def save_results(results):
    """Save results to a JSON file in the benchmarks folder."""
    # Create benchmarks directory if it doesn't exist
    os.makedirs('benchmarks', exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"benchmarks/benchmark_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)
    print()
    
    if "summary" in results:
        summary = results["summary"]
        print("PERFORMANCE SUMMARY:")
        if "peak_checker_rate_odd_per_sec" in summary:
            print(f"  Peak Rate (odd/s):       {summary['peak_checker_rate_odd_per_sec']:,.0f}")
            print(f"  Peak Rate (effective/s): {summary['peak_checker_rate_effective_per_sec']:,.0f}")
        if "peak_tuner_rate_odd_per_sec" in summary:
            print(f"  Tuner Peak (odd/s):      {summary['peak_tuner_rate_odd_per_sec']:,.0f}")
        if "optimal_config" in summary:
            print(f"\n  OPTIMAL CONFIGURATION:")
            for key, value in summary["optimal_config"].items():
                print(f"    {key}: {value}")
        print()
    
    print("SYSTEM SPECS:")
    specs = results["system_specs"]
    if "gpu" in specs and "name" in specs["gpu"]:
        print(f"  GPU: {specs['gpu']['name']}")
        print(f"  VRAM: {specs['gpu']['vram_total_gb']} GB")
        print(f"  Compute: {specs['gpu']['compute_capability']}")
    print()
    
    print(f"Results saved to: {filename}")
    print()
    print("=" * 70)
    print("THANK YOU FOR BENCHMARKING!")
    print("=" * 70)
    print(f"Please send '{filename}' back to the developer.")
    print("You can upload it to a file sharing service or paste the contents.")
    print("=" * 70)
    
    return filename

def main():
    """Main benchmark routine."""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║           COLLATZ ENGINE BENCHMARK UTILITY                        ║
║           Automated Performance Testing                           ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    print("This script will:")
    print("  1. Collect your system specifications")
    print("  2. Run the Collatz hybrid checker")
    print("  3. Run the auto-tuner to optimize settings")
    print("  4. Collect performance metrics")
    print("  5. Save everything to a results file")
    print()
    
    duration = input("How many minutes should the benchmark run? [default: 10]: ").strip()
    if not duration:
        duration = 10
    else:
        try:
            duration = int(duration)
        except:
            print("Invalid input, using default of 10 minutes")
            duration = 10
    
    print()
    print(f"Starting {duration}-minute benchmark...")
    print("Press Ctrl+C to stop early (results will still be saved)")
    print()
    
    input("Press Enter to begin...")
    print()
    
    # Run benchmark
    results = run_benchmark(duration_minutes=duration)
    
    # Mark benchmark as complete if system was optimized
    if optimization_state.is_system_optimized():
        optimization_state.mark_benchmark_complete()
        print("✓ Benchmark completed on optimized system")
    
    # Save results
    filename = save_results(results)
    
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBenchmark cancelled by user.")
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
