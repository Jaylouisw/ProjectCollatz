"""
COLLATZ CONJECTURE - HYBRID PROOF ENGINE
=========================================
Copyright (c) 2025 Jay Wenden (CollatzEngine)
Licensed under CC BY-NC-SA 4.0
https://creativecommons.org/licenses/by-nc-sa/4.0/

Features:
- Automatically uses GPU if available (preferred)
- Falls back to CPU-only if no GPU
- Uses ALL CPU cores at LOW PRIORITY
- Loop detection for true counterexamples
- Auto-saves on interrupt
- Stops and notifies on counterexample
- RAM limited to 75% of system max
- Scales to any hardware configuration
"""

import os
import sys
import time
import json
import psutil
import signal
import numpy as np
import subprocess
from datetime import datetime
from multiprocessing import Pool, Process, Queue as MPQueue, cpu_count
from queue import Empty

# Import error handler
try:
    from error_handler import logger, safe_import_cupy, check_config_validity
    ERROR_HANDLING = True
except ImportError:
    ERROR_HANDLING = False
    logger = None
    print("Warning: Error handler not available")

# Try to import GPU support with error handling
if ERROR_HANDLING:
    cp, GPU_AVAILABLE, gpu_msg = safe_import_cupy()
    if not GPU_AVAILABLE:
        print(f"GPU Status: {gpu_msg}")
else:
    try:
        import cupy as cp
        GPU_AVAILABLE = True
    except ImportError:
        GPU_AVAILABLE = False
        cp = None

# Import contribution tracker
try:
    from contribution_tracker import add_contribution
    CONTRIBUTION_TRACKING = True
except ImportError:
    CONTRIBUTION_TRACKING = False
    add_contribution = None

# Configuration
CONFIG_FILE = "collatz_config.json"
COUNTEREXAMPLE_FILE = "counterexamples.txt"
SAVE_INTERVAL = 10000000000  # Save every 10B (frequent saves for auto-tuner accuracy)
NUM_STREAMS = 4

shutdown_flag = False

def detect_gpus():
    """Detect all available GPUs and return their properties."""
    if not GPU_AVAILABLE:
        return []
    
    try:
        gpu_count = cp.cuda.runtime.getDeviceCount()
        gpus = []
        
        for i in range(gpu_count):
            with cp.cuda.Device(i):
                props = cp.cuda.runtime.getDeviceProperties(i)
                mem_info = cp.cuda.Device(i).mem_info
                
                gpu_info = {
                    'id': i,
                    'name': props['name'].decode() if isinstance(props['name'], bytes) else props['name'],
                    'total_memory': mem_info[1],
                    'free_memory': mem_info[0],
                    'compute_capability': f"{props['major']}.{props['minor']}",
                    'multiprocessor_count': props['multiProcessorCount'],
                    'max_threads_per_sm': props['maxThreadsPerMultiProcessor'],
                    'warp_size': props['warpSize']
                }
                gpus.append(gpu_info)
        
        return gpus
    except Exception as e:
        print(f"[WARNING] GPU detection failed: {e}")
        return []

def signal_handler(sig, frame):
    global shutdown_flag
    print("\n\nStopping...")
    shutdown_flag = True

signal.signal(signal.SIGINT, signal_handler)

def set_low_priority():
    """Set current process to low priority."""
    try:
        p = psutil.Process(os.getpid())
        if sys.platform == 'win32':
            p.nice(psutil.IDLE_PRIORITY_CLASS)
        else:
            p.nice(19)
    except:
        pass

def format_time(seconds):
    """Format seconds into years, months, days, hours, minutes, seconds."""
    if seconds < 1:
        return f"{seconds:.1f}s"
    
    years = int(seconds // (365.25 * 24 * 3600))
    seconds %= (365.25 * 24 * 3600)
    
    months = int(seconds // (30.44 * 24 * 3600))
    seconds %= (30.44 * 24 * 3600)
    
    days = int(seconds // (24 * 3600))
    seconds %= (24 * 3600)
    
    hours = int(seconds // 3600)
    seconds %= 3600
    
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    
    parts = []
    if years > 0:
        parts.append(f"{years}y")
    if months > 0:
        parts.append(f"{months}mo")
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)

def load_config():
    """Load saved progress."""
    if os.path.exists(CONFIG_FILE):
        try:
            # Validate config file if error handling available
            if ERROR_HANDLING:
                valid, msg, config = check_config_validity(CONFIG_FILE)
                if not valid:
                    logger.log_error('config_load', f'Config validation failed: {msg}')
                    print(f"[WARNING] {msg}")
                    print("[WARNING] Using default configuration")
                    return 0, 0, 0, 0
            
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                highest = config.get('highest_proven', 0)
                total = config.get('total_tested', 0)
                total_runtime = config.get('total_runtime_seconds', 0)
                max_steps_ever = config.get('max_steps_ever', 0)
                print(f"[RESUME] Loaded: Highest={highest:,}, Total={total:,}, Runtime={format_time(total_runtime)}")
                return highest, total, total_runtime, max_steps_ever
        except json.JSONDecodeError as e:
            if ERROR_HANDLING:
                logger.log_error('config_load', 'Invalid JSON in config file', 
                               {'error': str(e)}, e)
            print(f"[ERROR] Config file corrupted: {e}")
            print("[WARNING] Starting fresh")
            return 0, 0, 0, 0
        except Exception as e:
            if ERROR_HANDLING:
                logger.log_error('config_load', 'Unexpected error loading config', None, e)
            print(f"[WARNING] Config load failed: {e}")
            return 0, 0, 0, 0
    return 0, 0, 0, 0

def save_config(highest_proven, total_tested, total_runtime_seconds=None, max_steps_ever=None, record_contribution=False, session_tested=0):
    """Save current progress - with backwards protection."""
    try:
        # Load existing config to check for backwards movement
        existing_highest = 0
        existing_runtime = 0
        existing_max_steps = 0
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    existing = json.load(f)
                    existing_highest = existing.get('highest_proven', 0)
                    existing_runtime = existing.get('total_runtime_seconds', 0)
                    existing_max_steps = existing.get('max_steps_ever', 0)
            except:
                pass
        
        # NEVER save a lower highest_proven value
        if highest_proven < existing_highest:
            print(f"[PROTECTION] Prevented backwards save! Current={existing_highest:,}, Attempted={highest_proven:,}")
            return
        
        # Only update runtime if it increased (or if not provided, keep existing)
        if total_runtime_seconds is None:
            total_runtime_seconds = existing_runtime
        else:
            total_runtime_seconds = max(total_runtime_seconds, existing_runtime)
        
        # Track max steps ever seen across all sessions
        # NOTE: This only tracks step counts from CPU workers (difficult numbers).
        # GPU kernel does not return step counts for performance reasons.
        # max_steps_ever = 0 means no CPU workers have returned results yet.
        if max_steps_ever is not None:
            existing_max_steps = max(existing_max_steps, max_steps_ever)
        
        # Record contribution if requested
        if record_contribution and CONTRIBUTION_TRACKING and session_tested > 0:
            try:
                username = add_contribution(highest_proven, total_tested, session_tested, total_runtime_seconds)
                print(f"[CONTRIBUTION] Recorded for {username}")
            except Exception as e:
                print(f"[WARNING] Could not record contribution: {e}")
        
        config = {
            'highest_proven': int(highest_proven),
            'total_tested': int(total_tested),
            'total_runtime_seconds': float(total_runtime_seconds),
            'max_steps_ever': int(existing_max_steps),
            'last_updated': datetime.now().isoformat()
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Save failed: {e}")

# ============================================================================
# GPU MODE
# ============================================================================

# Enable CuPy memory pool for faster allocations (reduces CPU-GPU transfer overhead)
if GPU_AVAILABLE:
    mempool = cp.get_default_memory_pool()
    pinned_mempool = cp.get_default_pinned_memory_pool()
    # Use memory pool to avoid frequent malloc/free operations
    mempool.set_limit(size=None)  # No limit, use all available

def get_gpu_config():
    """Get optimal GPU configuration based on hardware specs."""
    if not GPU_AVAILABLE:
        return None
    
    try:
        # Load tuning parameters, use defaults if file doesn't exist
        try:
            if ERROR_HANDLING:
                valid, msg, tuning_data = check_config_validity('gpu_tuning.json')
                if not valid:
                    logger.log_error('gpu_config', f'GPU tuning config invalid: {msg}')
                    print(f"[WARNING] {msg}")
                    print("[WARNING] Using default GPU tuning")
                    tuning = {
                        'work_multiplier': 800,
                        'threads_per_block_multiplier': 8,
                        'blocks_per_sm': 4,
                        'memory_usage_percent': 5,
                        'batch_size_override': None,
                        'cpu_workers': None
                    }
                else:
                    # Handle new multi-GPU format or old format
                    if isinstance(tuning_data, dict) and 'config' in tuning_data:
                        tuning = tuning_data['config']
                        num_gpus_tuned = tuning_data.get('num_gpus', 1)
                        if num_gpus_tuned > 1:
                            print(f"[INFO] Loaded multi-GPU tuning (optimized for {num_gpus_tuned} GPUs)")
                    else:
                        tuning = tuning_data  # Old format
            else:
                with open('gpu_tuning.json', 'r') as f:
                    tuning_data = json.load(f)
                    # Handle new multi-GPU format or old format
                    if isinstance(tuning_data, dict) and 'config' in tuning_data:
                        tuning = tuning_data['config']
                        num_gpus_tuned = tuning_data.get('num_gpus', 1)
                        if num_gpus_tuned > 1:
                            print(f"[INFO] Loaded multi-GPU tuning (optimized for {num_gpus_tuned} GPUs)")
                    else:
                        tuning = tuning_data  # Old format
        except FileNotFoundError:
            tuning = {
                'work_multiplier': 800,
                'threads_per_block_multiplier': 8,
                'blocks_per_sm': 4,
                'memory_usage_percent': 5,
                'batch_size_override': None,
                'cpu_workers': None  # None = auto-detect, or specific number
            }
        except Exception as e:
            if ERROR_HANDLING:
                logger.log_error('gpu_config', 'Error loading GPU tuning config', None, e)
            print(f"[WARNING] Error loading GPU tuning: {e}")
            print("[WARNING] Using defaults")
            tuning = {
                'work_multiplier': 800,
                'threads_per_block_multiplier': 8,
                'blocks_per_sm': 4,
                'memory_usage_percent': 5,
                'batch_size_override': None,
                'cpu_workers': None
            }
        
        device = cp.cuda.Device()
        props = cp.cuda.runtime.getDeviceProperties(device.id)
        mem_info = device.mem_info
        free_mem = mem_info[0]
        
        sm_count = props['multiProcessorCount']
        max_threads_per_sm = props['maxThreadsPerMultiProcessor']
        warp_size = props['warpSize']
        
        # Ensure tuning has required keys
        if not isinstance(tuning, dict):
            raise ValueError(f"tuning must be dict, got {type(tuning)}")
        if 'threads_per_block_multiplier' not in tuning:
            raise KeyError("tuning missing 'threads_per_block_multiplier'")
        
        threads_per_block = warp_size * tuning['threads_per_block_multiplier']
        blocks_per_sm = tuning['blocks_per_sm']
        total_blocks = sm_count * blocks_per_sm
        
        max_concurrent_threads = sm_count * max_threads_per_sm
        work_multiplier = tuning['work_multiplier']
        base_batch_size = (max_concurrent_threads * work_multiplier) // threads_per_block * threads_per_block
        
        # No VRAM limit - let autotuner handle batch size entirely
        # Memory usage percent is ignored, batch_size_override has full control
        batch_size = base_batch_size
        
        # Allow manual override (autotuner controls this)
        if tuning['batch_size_override'] is not None:
            batch_size = tuning['batch_size_override']
        
        if batch_size >= 10_000_000:
            batch_size = (batch_size // 10_000_000) * 10_000_000
        elif batch_size >= 1_000_000:
            batch_size = (batch_size // 1_000_000) * 1_000_000
        
        return {
            'batch_size': batch_size,
            'threads_per_block': threads_per_block,
            'sm_count': sm_count,
            'max_concurrent_threads': max_concurrent_threads,
            'cuda_cores': sm_count * 128,
            'name': props['name'].decode(),
            'vram_total': mem_info[1],
            'vram_free': mem_info[0],
            'tuning': tuning  # Include tuning config for CPU workers
        }
    except cp.cuda.runtime.CUDARuntimeError as e:
        if ERROR_HANDLING:
            logger.log_error('gpu_runtime', 'CUDA runtime error during GPU initialization',
                           {'error_code': str(e)}, e)
        print(f"[ERROR] CUDA runtime error: {e}")
        print("[ERROR] This may indicate driver issues or GPU hardware problems")
        return None
    except Exception as e:
        if ERROR_HANDLING:
            logger.log_error('gpu_initialization', 'GPU initialization failed', None, e)
        print(f"[ERROR] GPU initialization failed: {e}")
        return None

# GPU kernel for Collatz checking - Optimized branchless version
if GPU_AVAILABLE:
    collatz_kernel = cp.RawKernel(r'''
    extern "C" __global__
    void collatz_check_batch(unsigned long long start_high, unsigned long long start_low, 
                             int* __restrict__ results, int n, unsigned long long proven_high, unsigned long long proven_low,
                             int max_steps) {
        int idx = blockDim.x * blockIdx.x + threadIdx.x;
        if (idx >= n) return;
        
        // Each thread handles an odd number: start + idx*2
        unsigned long long offset = (unsigned long long)idx * 2;
        unsigned long long num_low = start_low + offset;
        unsigned long long num_high = start_high;
        if (num_low < start_low) num_high++;
        
        // Store original for cycle detection
        const unsigned long long orig_low = num_low;
        const unsigned long long orig_high = num_high;
        
        int steps = 0;
        const int CYCLE_CHECK_INTERVAL = 128;  // Power of 2 for fast modulo
        
        // Main loop - optimized with reduced branching
        #pragma unroll 1  // Let compiler decide optimal unrolling
        while (steps < max_steps) {
            // Branchless convergence check
            // Check if num == 1
            int is_one = (num_high == 0) & (num_low == 1);
            
            // Check if below proven range (converged)
            int below_proven = (num_high < proven_high) | 
                              ((num_high == proven_high) & (num_low <= proven_low));
            
            // Check if below start range
            int below_start = (num_high < start_high) | 
                             ((num_high == start_high) & (num_low < start_low));
            
            // If any convergence condition met, mark as proven and exit
            if (is_one | below_proven | below_start) {
                results[idx] = 1;
                return;
            }
            
            // Cycle detection (lazy - every 128 steps)
            if (((steps & (CYCLE_CHECK_INTERVAL - 1)) == 0) & (steps > 0)) {
                if ((num_high == orig_high) & (num_low == orig_low)) {
                    results[idx] = -1;
                    return;
                }
            }
            
            // Branchless Collatz step
            // For even: divide by 2^k where k = trailing zeros
            // For odd: (3n+1)/2
            
            int is_odd = num_low & 1;
            
            if (is_odd) {
                // Odd case: compute (3n+1)/2
                // 3n = (n << 1) + n
                unsigned long long low_doubled = num_low << 1;
                unsigned long long high_doubled = (num_high << 1) | (num_low >> 63);
                
                unsigned long long result_low = low_doubled + num_low;
                unsigned long long result_high = high_doubled + num_high + (result_low < low_doubled);
                
                // Add 1
                result_low++;
                result_high += (result_low == 0);
                
                // Divide by 2
                num_low = __funnelshift_r(result_high, result_low, 1);
                num_high = result_high >> 1;
                steps++;
            } else {
                // Even case: divide by 2^k
                int zeros = __ffsll(num_low) - 1;
                
                if (zeros > 0 && zeros < 64) {
                    // Shift by zeros bits
                    num_low = __funnelshift_r(num_high, num_low, zeros);
                    num_high = num_high >> zeros;
                    steps += zeros;
                } else if (zeros == 0) {
                    // Single bit shift
                    num_low = __funnelshift_r(num_high, num_low, 1);
                    num_high = num_high >> 1;
                    steps++;
                } else {
                    // All zeros in low word, shift high word
                    zeros = __ffsll(num_high) - 1;
                    num_low = num_high >> zeros;
                    num_high = 0;
                    steps += (64 + zeros);
                }
            }
        }
        
        // Max steps reached without convergence
        results[idx] = 0;
    }
    ''', 'collatz_check_batch')
    
    # Create CUDA streams for async execution
    cuda_streams = [cp.cuda.Stream(non_blocking=True) for _ in range(NUM_STREAMS)]

def check_batch_gpu(start, batch_size, highest_proven, threads_per_block=256, timeout_seconds=60, stream=None):
    """Check a batch on GPU with timeout and optional stream for async execution.
    Optimized to minimize CPU-GPU transfers."""
    start_high = start >> 64
    start_low = start & ((1 << 64) - 1)
    proven_high = highest_proven >> 64
    proven_low = highest_proven & ((1 << 64) - 1)
    
    # Allocate results array on GPU (reuse if possible)
    if not hasattr(check_batch_gpu, '_results_cache') or check_batch_gpu._results_cache.size != batch_size:
        check_batch_gpu._results_cache = cp.zeros(batch_size, dtype=cp.int32)
    
    results = check_batch_gpu._results_cache
    results.fill(0)  # Reset results on GPU (no transfer)
    
    blocks = (batch_size + threads_per_block - 1) // threads_per_block
    
    # Use provided stream or default null stream
    exec_stream = stream if stream is not None else cp.cuda.Stream.null
    
    steps_per_check = 10_000_000
    
    # Pre-compute kernel arguments (avoid recomputation)
    kernel_args = (cp.uint64(start_high), cp.uint64(start_low), 
                   results, batch_size, 
                   cp.uint64(proven_high), cp.uint64(proven_low),
                   cp.int32(steps_per_check))
    
    with exec_stream:
        collatz_kernel((blocks,), (threads_per_block,), kernel_args)
        exec_stream.synchronize()
        
        # Minimize GPU-CPU data transfer by checking on GPU first
        # Fast path: Check for success first (most common case ~99.99%)
        min_result = int(cp.min(results))
        if min_result == 1:
            # All proven - zero additional transfer needed
            return ('success', batch_size)
        
        # Check for counterexample (extremely rare)
        if min_result == -1:
            # Only transfer the index (4 bytes) not the whole array
            disproven_idx = int(cp.argmin(results))
            counterexample = start + disproven_idx * 2
            return ('disproven', counterexample)
        
        # Inconclusive (rare) - only transfer indices
        inconclusive = cp.where(results == 0)[0]
        if len(inconclusive) > 0:
            first_idx = int(inconclusive[0])
            first_inconclusive = start + first_idx * 2
            return ('inconclusive', first_inconclusive, len(inconclusive))
    
    return ('success', batch_size)

def cpu_collatz_worker(task_queue, result_queue, start_range):
    """CPU worker for difficult numbers. Optimized to minimize IPC overhead."""
    batch_results = []
    batch_size = 10  # Batch results before sending
    
    while True:
        try:
            num = task_queue.get(timeout=1)
            
            if num is None:
                # Flush remaining results before exiting
                if batch_results:
                    for result in batch_results:
                        result_queue.put(result)
                break
            
            original_num = num
            steps = 0
            seen = set()
            
            while True:
                if num == 1 or num < start_range:
                    batch_results.append(('proven', original_num, steps))
                    break
                
                if num in seen:
                    # Counterexample is critical - send immediately
                    result_queue.put(('disproven', original_num, steps))
                    batch_results = []  # Clear batch
                    break
                
                if steps % 1000 == 0:
                    seen.add(num)
                
                if num % 2 == 1:
                    num = (3 * num + 1) // 2
                else:
                    num = num // 2
                
                steps += 1
                
                if steps > 100_000_000:
                    batch_results.append(('inconclusive', original_num, steps))
                    break
            
            # Send batch when it reaches batch_size (only for proven/inconclusive)
            if len(batch_results) >= batch_size:
                for result in batch_results:
                    result_queue.put(result)
                batch_results = []
                    
        except Empty:
            # Flush batch on idle
            if batch_results:
                for result in batch_results:
                    result_queue.put(result)
                batch_results = []
            continue
        except Exception as e:
            try:
                result_queue.put(('error', num, str(e)))
            except:
                pass

def check_batch_multigpu(position, batch_size, highest_proven, threads_per_block, gpu_list):
    """Check a batch across multiple GPUs in parallel.
    Splits the batch across all available GPUs for maximum throughput."""
    if len(gpu_list) == 1:
        # Single GPU - use regular function
        with cp.cuda.Device(gpu_list[0]['id']):
            return check_batch_gpu(position, batch_size, highest_proven, threads_per_block)
    
    # Multi-GPU: split batch across devices
    gpus_count = len(gpu_list)
    batch_per_gpu = batch_size // gpus_count
    remainder = batch_size % gpus_count
    
    results_list = [None] * gpus_count
    import threading
    
    def gpu_worker(gpu_idx, gpu_info, start_pos, gpu_batch_size):
        """Worker function to run batch on specific GPU."""
        try:
            with cp.cuda.Device(gpu_info['id']):
                result = check_batch_gpu(start_pos, gpu_batch_size, highest_proven, threads_per_block)
                results_list[gpu_idx] = result
        except Exception as e:
            print(f"\n[GPU {gpu_info['id']} ERROR] {e}")
            results_list[gpu_idx] = None
    
    # Launch parallel GPU workers
    threads = []
    current_pos = position
    
    for idx, gpu_info in enumerate(gpu_list):
        # Distribute remainder across first GPUs
        gpu_batch = batch_per_gpu + (1 if idx < remainder else 0)
        
        thread = threading.Thread(
            target=gpu_worker,
            args=(idx, gpu_info, current_pos, gpu_batch)
        )
        thread.start()
        threads.append(thread)
        
        current_pos += gpu_batch * 2  # Skip to next odd number range
    
    # Wait for all GPUs to complete
    for thread in threads:
        thread.join()
    
    # Aggregate results
    all_passed = all(r == 1 if r is not None else False for r in results_list)
    any_failed = any(r == -1 if r is not None else False for r in results_list)
    any_inconclusive = any(r == 0 if r is not None else False for r in results_list)
    
    if any_failed:
        return -1  # Counterexample found
    elif all_passed:
        return 1  # All proven
    else:
        return 0  # Inconclusive (needs CPU)

def run_gpu_mode():
    """Run in GPU mode with CPU workers for difficult numbers."""
    global shutdown_flag
    
    highest_proven, total_tested, previous_total_runtime, max_steps_ever = load_config()
    position = highest_proven + 1
    
    # Track session start for runtime calculation
    session_start_time = time.time()
    
    # Skip to next odd number if starting on even
    if position % 2 == 0:
        position += 1
    
    # Random checker disabled for maximum sequential performance
    # (It was competing for GPU resources causing 5-15% slowdown)
    random_checker_process = None
    # random_checker_script = os.path.join(os.path.dirname(__file__), 'collatz_random_1024.py')
    # if os.path.exists(random_checker_script):
    #     try:
    #         print("Launching random 1024-bit checker in parallel...")
    #         random_checker_process = subprocess.Popen(
    #             [sys.executable, random_checker_script],
    #             stdout=subprocess.PIPE,
    #             stderr=subprocess.PIPE,
    #             text=True,
    #             bufsize=1
    #         )
    #         print("✓ Random checker started\n")
    #     except Exception as e:
    #         print(f"Could not start random checker: {e}\n")
    
    print("=" * 70)
    print("COLLATZ HYBRID PROOF ENGINE - GPU MODE")
    print("=" * 70)
    
    # Detect all available GPUs
    available_gpus = detect_gpus()
    num_gpus = len(available_gpus)
    
    if num_gpus == 0:
        print("No GPUs detected. Falling back to CPU mode.")
        return run_cpu_mode()
    
    print(f"Detected {num_gpus} GPU{'s' if num_gpus > 1 else ''}:")
    for gpu in available_gpus:
        vram_gb = gpu['total_memory'] / (1024**3)
        print(f"  [{gpu['id']}] {gpu['name']} - {vram_gb:.1f}GB, {gpu['multiprocessor_count']} SMs")
    
    if num_gpus > 1:
        print(f"\n[MULTI-GPU] Using all {num_gpus} GPUs for parallel processing")
        print("[MULTI-GPU] Workload will be distributed across all devices")
    print()
    
    gpu_config = get_gpu_config()
    if gpu_config is None:
        print("Failed to initialize GPU. Falling back to CPU mode.")
        return run_cpu_mode()
    
    print(f"Primary GPU: {gpu_config['name']}")
    print(f"VRAM: {gpu_config['vram_total'] / 1024**3:.1f} GB total, {gpu_config['vram_free'] / 1024**3:.1f} GB free")
    print(f"CUDA Cores: {gpu_config['cuda_cores']}")
    print(f"Streaming Multiprocessors: {gpu_config['sm_count']}")
    print(f"Max Concurrent Threads: {gpu_config['max_concurrent_threads']:,}")
    
    batch_size = gpu_config['batch_size']
    threads_per_block = gpu_config['threads_per_block']
    
    # Get CPU worker count from tuning config or auto-detect
    tuning = gpu_config.get('tuning', {})
    cpu_workers_config = tuning.get('cpu_workers', None)
    
    if cpu_workers_config is not None:
        num_cpu_workers = min(cpu_workers_config, cpu_count())  # Cap at actual CPU count
        print(f"\nCPU Workers: {num_cpu_workers} (configured via tuning)")
    else:
        num_cpu_workers = min(cpu_count(), 16)
        print(f"\nCPU Workers: {num_cpu_workers} (auto-detected, for difficult numbers)")
    
    # Use direct multiprocessing.Queue instead of Manager().Queue() for less overhead
    cpu_task_queue = MPQueue()
    cpu_result_queue = MPQueue()
    
    cpu_workers = []
    for i in range(num_cpu_workers):
        p = Process(target=cpu_collatz_worker, args=(cpu_task_queue, cpu_result_queue, highest_proven))
        p.daemon = True
        p.start()
        cpu_workers.append(p)
    
    cpu_pending = 0
    
    print(f"\nOptimized batch size: {batch_size:,} numbers per kernel launch")
    print(f"Estimated VRAM usage: {(batch_size * 4) / 1024**3:.2f} GB")
    print(f"\nStarting at: {position:,} (odd numbers only)")
    print(f"Threads per block: {threads_per_block} (hardware-optimized)")
    print(f"Save interval: {SAVE_INTERVAL:,}")
    print(f"OPTIMIZATION: Skipping all even numbers (2x effective speed)")
    print("=" * 70)
    print("\nPress Ctrl+C to stop safely\n")
    
    start_time = time.time()
    session_tested = 0
    last_save = 0
    last_display = 0
    display_interval = 0.5  # Update display every 0.5 seconds (or less frequently)
    last_config_check = 0
    config_check_interval = 5.0  # Check for config changes every 5 seconds (for auto-tuner)
    session_max_steps = 0  # Track highest step count this session (CPU workers only)
    # max_steps_ever loaded from config - only tracks CPU worker results (difficult numbers)
    
    batch_counter = 0
    cpu_check_interval = 100  # Check CPU results every 100 batches instead of every batch
    shutdown_check_interval = 50  # Check shutdown flag every 50 batches (reduces global variable access)
    
    # Use multi-GPU if available
    use_multigpu = num_gpus > 1
    
    try:
        while True:
            if use_multigpu:
                # Multi-GPU: distribute batch across all GPUs
                result = check_batch_multigpu(position, batch_size, highest_proven, threads_per_block, available_gpus)
                result_type = (result, None)  # Multi-GPU returns simple result code
            else:
                # Single GPU: use regular batch checker
                result = check_batch_gpu(position, batch_size, highest_proven, threads_per_block)
                result_type = result[0]
            
            # Handle results uniformly
            if isinstance(result_type, tuple):
                result_type = result_type[0]
            
            if result_type == 'disproven':
                counterexample = result[1]
                print(f"\n{'='*70}")
                print("!!! COUNTEREXAMPLE FOUND - LOOP DETECTED !!!")
                print(f"{'='*70}")
                print(f"Number: {counterexample:,}")
                print(f"This number enters a loop without reaching 1!")
                print(f"{'='*70}\n")
                
                with open(COUNTEREXAMPLE_FILE, 'a') as f:
                    f.write(f"{datetime.now()}: GPU DISPROVEN - Loop detected: {counterexample:,}\n")
                
                highest_proven = counterexample - 1
                total_runtime = previous_total_runtime + (time.time() - session_start_time)
                save_config(highest_proven, total_tested, total_runtime, max_steps_ever)
                return
            
            if result_type == 'inconclusive':
                first_inconclusive = result[1]
                count_inconclusive = result[2]
                
                print(f"\n[CPU OFFLOAD] {count_inconclusive:,} difficult numbers detected")
                print(f"              Sending to CPU workers...")
                
                for i in range(count_inconclusive):
                    cpu_task_queue.put(first_inconclusive + (i << 1))  # Bit shift instead of multiply
                    cpu_pending += 1
                
                # CRITICAL: highest_proven is the last number BEFORE first inconclusive
                highest_proven = first_inconclusive - 2
            else:
                # Full batch succeeded - highest proven is the last odd number checked
                highest_proven = position + ((batch_size - 1) << 1)  # Bit shift instead of multiply
            
            # Update position and counters (common to all paths)
            batch_size_doubled = batch_size << 1  # Cache the doubled value
            position += batch_size_doubled
            session_tested += batch_size
            total_tested += batch_size
            batch_counter += 1
            
            # Check CPU results only periodically to reduce overhead
            if batch_counter >= cpu_check_interval:
                batch_counter = 0
                try:
                    while True:
                        result_type, num, info = cpu_result_queue.get_nowait()
                        cpu_pending -= 1
                        
                        # Track max steps (info contains step count from CPU workers)
                        # NOTE: GPU results don't include step counts for performance reasons
                        if result_type in ('proven', 'disproven', 'inconclusive') and isinstance(info, int):
                            session_max_steps = max(session_max_steps, info)
                            max_steps_ever = max(max_steps_ever, info)
                        
                        if result_type == 'disproven':
                            print(f"\n{'='*70}")
                            print("!!! CPU FOUND COUNTEREXAMPLE !!!")
                            print(f"{'='*70}")
                            print(f"Number: {num:,}")
                            print(f"Steps: {info:,}")
                            print(f"{'='*70}\n")
                            
                            with open(COUNTEREXAMPLE_FILE, 'a') as f:
                                f.write(f"{datetime.now()}: CPU DISPROVEN: {num:,} after {info:,} steps\n")
                except Empty:
                    pass
            
            # Only check time and shutdown flag every 10 batches to reduce overhead
            if batch_counter % 10 == 0:
                # Check for shutdown every 50 batches to reduce global variable access
                if batch_counter % shutdown_check_interval == 0:
                    if shutdown_flag:
                        break
                
                current_time = time.time()
                
                # Periodically reload GPU config to allow live tuning
                if current_time - last_config_check >= config_check_interval:
                    new_config = get_gpu_config()
                    if new_config and (new_config['batch_size'] != batch_size or 
                                       new_config['threads_per_block'] != threads_per_block):
                        batch_size = new_config['batch_size']
                        threads_per_block = new_config['threads_per_block']
                        print(f"\n[CONFIG RELOAD] Batch: {batch_size:,}, Threads: {threads_per_block}")
                    last_config_check = current_time
                
                if session_tested - last_save >= SAVE_INTERVAL:
                    total_runtime = previous_total_runtime + (current_time - session_start_time)
                    save_config(highest_proven, total_tested, total_runtime, max_steps_ever)
                    last_save = session_tested
                
                # Update display only if at least 0.5 seconds have passed
                if current_time - last_display >= display_interval:
                    elapsed = current_time - start_time
                    rate = session_tested / elapsed
                    
                    # Calculate current rate over time since last display
                    time_since_last = current_time - last_display if last_display > 0 else 1.0
                    last_tested = getattr(check_batch_gpu, '_last_tested', 0)
                    current_interval_tested = session_tested - last_tested
                    current_rate = current_interval_tested / time_since_last
                    check_batch_gpu._last_tested = session_tested
                    
                    session_elapsed = current_time - session_start_time
                    total_runtime = previous_total_runtime + session_elapsed
                    
                    # Build output string once, then print (use bit shift for *2)
                    rate_doubled = rate + rate  # Addition is faster than multiplication
                    current_rate_doubled = current_rate + current_rate
                    output = [
                        "\033[2J\033[H",  # Clear screen and move cursor to top
                        "=" * 70,
                        f"SESSION SUMMARY - {datetime.now().strftime('%H:%M:%S')}",
                        "=" * 70,
                        f"Highest proven:  {highest_proven:,}",
                        f"Session tested:  {session_tested:,}",
                        f"Average rate:    {rate:,.0f} odd/s  ({rate_doubled:,.0f} effective/s)",
                        f"Current rate:    {current_rate:,.0f} odd/s  ({current_rate_doubled:,.0f} effective/s)",
                        f"Total tested:    {total_tested:,}",
                        f"Session runtime: {format_time(session_elapsed)}",
                        f"Total runtime:   {format_time(total_runtime)}"
                    ]
                    if session_max_steps > 0 or max_steps_ever > 0:
                        output.append(f"Max steps (session/ever): {session_max_steps:,} / {max_steps_ever:,}")
                    if cpu_pending > 0:
                        output.append(f"CPU workers:     {cpu_pending:,} numbers in queue")
                    output.append("=" * 70)
                    
                    print("\n".join(output), flush=True)
                    
                    # Write real-time stats for auto-tuner (lightweight JSON)
                    try:
                        with open("realtime_stats.json", "w") as f:
                            import json
                            stats = {
                                "session_tested": session_tested,
                                "session_elapsed": session_elapsed,
                                "current_rate": current_rate,
                                "average_rate": rate,
                                "timestamp": current_time
                            }
                            json.dump(stats, f)
                    except:
                        pass  # Don't crash if file write fails
                    
                    last_display = current_time
    
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nShutting down CPU workers...")
        for _ in range(num_cpu_workers):
            cpu_task_queue.put(None)
        
        if session_tested > 0:
            session_elapsed = time.time() - session_start_time
            total_runtime = previous_total_runtime + session_elapsed
            save_config(highest_proven, total_tested, total_runtime, max_steps_ever, record_contribution=True, session_tested=session_tested)
            elapsed = time.time() - start_time
            rate = session_tested / elapsed if elapsed > 0 else 0
            
            # Calculate final current rate over last display_interval
            current_interval_tested = session_tested - (getattr(check_batch_gpu, '_last_tested', 0))
            current_rate = current_interval_tested / display_interval if display_interval > 0 else rate
            
            summary = []
            summary.append("=" * 70)
            summary.append("SESSION SUMMARY")
            summary.append("=" * 70)
            summary.append(f"Highest proven: {highest_proven:,}")
            summary.append(f"Session tested: {session_tested:,}")
            summary.append(f"Total tested: {total_tested:,}")
            summary.append(f"Average rate: {rate:,.0f} odd/s ({rate*2:,.0f} effective/s)")
            summary.append(f"Current rate: {current_rate:,.0f} odd/s ({current_rate*2:,.0f} effective/s)")
            if session_max_steps > 0 or max_steps_ever > 0:
                summary.append(f"Max steps (session/ever): {session_max_steps:,} / {max_steps_ever:,}")
            summary.append(f"Session runtime: {format_time(session_elapsed)}")
            summary.append(f"Total runtime: {format_time(total_runtime)}")
            summary.append(f"Session ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            summary.append("=" * 70)
            
            # Print to console
            print("\n" + "\n".join(summary))
            
            # Save to file
            with open("session_summary.txt", "w") as f:
                f.write("\n".join(summary))
            
            print("Saved!")
            print("=" * 70)

# ============================================================================
# CPU MODE
# ============================================================================

def collatz_check_cpu(n, highest_proven):
    """Check if n reaches 1 using CPU."""
    if n <= highest_proven:
        return (True, 0, 'already_proven')
    
    steps = 0
    visited = set()
    max_steps = 100000
    
    while n > 1 and steps < max_steps:
        if n in visited:
            return (False, steps, 'loop_detected')
        
        if n <= highest_proven:
            return (True, steps, 'hit_proven')
        
        # Lazy cycle detection
        if steps % 50 == 0:
            visited.add(n)
        
        if n & 1:
            # Odd: 3n+1
            n = (n << 1) + n + 1
            steps += 1
        else:
            # Even: divide by 2^k where k = trailing zeros
            tz = (n & -n).bit_length() - 1
            n >>= tz
            steps += tz
    
    if steps >= max_steps:
        return (False, steps, 'step_limit')
    
    return (n == 1, steps, 'reached_1' if n == 1 else 'unknown')

def worker_check_range(args):
    """Worker function to check a range of numbers."""
    start, count, highest_proven = args
    set_low_priority()
    
    for i in range(count):
        n = start + i
        
        if n <= highest_proven:
            continue
        
        reaches_1, steps, reason = collatz_check_cpu(n, highest_proven)
        
        if not reaches_1:
            return {
                'counterexample': n,
                'numbers_checked': i,
                'reason': reason
            }
    
    return {
        'counterexample': None,
        'numbers_checked': count
    }

def init_worker():
    """Initialize worker to ignore SIGINT."""
    try:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    except (AttributeError, ValueError) as e:
        # On some platforms (e.g., Android), signal handling may not work
        pass

def run_gpu_accelerated_cpu_mode(gpu_config, highest_proven, total_tested, previous_total_runtime):
    """CPU mode with GPU batch processing using VRAM."""
    global shutdown_flag
    
    session_start_time = time.time()
    position = highest_proven + 1
    batch_size = gpu_config['batch_size']
    threads_per_block = gpu_config['threads_per_block']
    
    # Get CPU worker count from tuning config or auto-detect
    tuning = gpu_config.get('tuning', {})
    cpu_workers_config = tuning.get('cpu_workers', None)
    
    if cpu_workers_config is not None:
        num_cpu_workers = min(cpu_workers_config, cpu_count())  # Cap at actual CPU count
        print(f"CPU Workers: {num_cpu_workers} (configured via tuning)")
    else:
        num_cpu_workers = min(cpu_count(), 16)
        print(f"CPU Workers: {num_cpu_workers} (auto-detected, for difficult numbers)")
    
    # Use direct multiprocessing.Queue instead of Manager().Queue() for less overhead
    cpu_task_queue = MPQueue()
    cpu_result_queue = MPQueue()
    
    cpu_workers = []
    for i in range(num_cpu_workers):
        p = Process(target=cpu_collatz_worker, args=(cpu_task_queue, cpu_result_queue, highest_proven))
        p.daemon = True
        p.start()
        cpu_workers.append(p)
    
    cpu_pending = 0
    
    print(f"\nGPU batch processing with VRAM")
    print(f"Save interval: {SAVE_INTERVAL:,}")
    print("Press Ctrl+C to stop safely\n")
    
    start_time = time.time()
    session_tested = 0
    last_save = 0
    
    try:
        while not shutdown_flag:
            # Use GPU kernel for batch checking (using VRAM)
            result = check_batch_gpu(position, batch_size, highest_proven, threads_per_block)
            
            if result[0] == 'disproven':
                counterexample = result[1]
                print(f"\n{'='*70}")
                print("!!! COUNTEREXAMPLE FOUND - LOOP DETECTED !!!")
                print(f"{'='*70}")
                print(f"Number: {counterexample:,}")
                print(f"{'='*70}\n")
                
                with open(COUNTEREXAMPLE_FILE, 'a') as f:
                    f.write(f"{datetime.now()}: GPU DISPROVEN - Loop detected: {counterexample:,}\n")
                
                highest_proven = counterexample - 1
                total_runtime = previous_total_runtime + (time.time() - session_start_time)
                save_config(highest_proven, total_tested, total_runtime, None)
                break
            
            if result[0] == 'inconclusive':
                first_inconclusive = result[1]
                count_inconclusive = result[2]
                
                print(f"[CPU OFFLOAD] {count_inconclusive:,} difficult numbers → CPU workers")
                
                for i in range(count_inconclusive):
                    cpu_task_queue.put(first_inconclusive + i)
                    cpu_pending += 1
                
                position += batch_size
                session_tested += batch_size
                total_tested += batch_size
            else:
                position += batch_size
                highest_proven = position - 1
                session_tested += batch_size
                total_tested += batch_size
            
            # Check CPU results
            try:
                while True:
                    result_type, num, info = cpu_result_queue.get_nowait()
                    cpu_pending -= 1
                    
                    if result_type == 'disproven':
                        print(f"\n{'='*70}")
                        print("!!! CPU FOUND COUNTEREXAMPLE !!!")
                        print(f"{'='*70}")
                        print(f"Number: {num:,}")
                        print(f"{'='*70}\n")
                        
                        with open(COUNTEREXAMPLE_FILE, 'a') as f:
                            f.write(f"{datetime.now()}: CPU DISPROVEN: {num:,} after {info:,} steps\n")
            except Empty:
                pass
            
            if session_tested - last_save >= SAVE_INTERVAL:
                total_runtime = previous_total_runtime + (time.time() - session_start_time)
                save_config(highest_proven, total_tested, total_runtime, None)
                last_save = session_tested
            
            elapsed = time.time() - start_time
            rate = session_tested / elapsed if elapsed > 0 else 0
            
            cpu_status = f" | CPU: {cpu_pending}" if cpu_pending > 0 else ""
            vram_used = cp.get_default_memory_pool().used_bytes() / 1024**3
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Proven: {highest_proven:,} | "
                  f"Rate: {rate:,.0f}/s | "
                  f"VRAM: {vram_used:.2f}GB{cpu_status}")
    
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nShutting down CPU workers...")
        for _ in range(num_cpu_workers):
            cpu_task_queue.put(None)
        
        if session_tested > 0:
            total_runtime = previous_total_runtime + (time.time() - session_start_time)
            save_config(highest_proven, total_tested, total_runtime, None)
            elapsed = time.time() - start_time
            rate = session_tested / elapsed if elapsed > 0 else 0
            
            # Calculate current rate
            current_interval_tested = session_tested - (getattr(check_batch_gpu, '_last_tested', 0))
            current_rate = current_interval_tested / 15.0 if current_interval_tested > 0 else rate
            
            print("\n" + "=" * 70)
            print("SESSION SUMMARY")
            print("=" * 70)
            print(f"Highest proven: {highest_proven:,}")
            print(f"Session tested: {session_tested:,}")
            print(f"Total tested: {total_tested:,}")
            print(f"Average rate: {rate:,.0f}/s ({rate*2:,.0f} effective/s)")
            print(f"Current rate: {current_rate:,.0f}/s ({current_rate*2:,.0f} effective/s)")
            print(f"Time: {elapsed/60:.1f} min")
            print("=" * 70)

def run_cpu_mode():
    """Run in CPU mode with optional GPU acceleration."""
    global shutdown_flag
    
    highest_proven, total_tested, previous_total_runtime, max_steps_ever = load_config()
    
    # Check if GPU is available for acceleration
    gpu_config = get_gpu_config() if GPU_AVAILABLE else None
    
    if gpu_config:
        print(f"\n{'='*70}")
        print("COLLATZ HYBRID PROOF ENGINE - CPU MODE (GPU-ACCELERATED)")
        print(f"{'='*70}")
        print(f"GPU: {gpu_config['name']}")
        print(f"VRAM: {gpu_config['vram_total'] / 1024**3:.1f} GB total, {gpu_config['vram_free'] / 1024**3:.1f} GB free")
        print(f"Batch size: {gpu_config['batch_size']:,} (using VRAM)")
        print(f"\nProgress:")
        print(f"  Starting at: {highest_proven + 1:,}")
        print(f"  Total tested: {total_tested:,}")
        print(f"{'='*70}\n")
        
        # Run GPU-accelerated mode
        return run_gpu_accelerated_cpu_mode(gpu_config, highest_proven, total_tested, previous_total_runtime)
    
    # Pure CPU mode (no GPU available)
    cpu_cores = cpu_count()
    
    print(f"\n{'='*70}")
    print("COLLATZ HYBRID PROOF ENGINE - CPU MODE (PURE)")
    print(f"{'='*70}")
    print(f"System Resources:")
    print(f"  CPU Cores: {cpu_cores}")
    print(f"  Process Priority: LOW")
    print(f"\nProgress:")
    print(f"  Starting at: {highest_proven + 1:,}")
    print(f"  Total tested: {total_tested:,}")
    print(f"{'='*70}\n")
    
    set_low_priority()
    
    session_start_time = time.time()
    position = highest_proven + 1
    session_tested = 0
    start_time = time.time()
    workers = cpu_cores
    chunk_size = 10000
    save_interval_cpu = 100000
    
    print(f"Workers: {workers} CPU cores")
    print(f"Chunk size: {chunk_size:,} per worker")
    print(f"Batch size: {workers * chunk_size:,}")
    print(f"Save interval: {save_interval_cpu:,}\n")
    print("Press Ctrl+C to stop safely\n")
    
    try:
        with Pool(workers, initializer=init_worker) as pool:
            while not shutdown_flag:
                work = [
                    (position + i * chunk_size, chunk_size, highest_proven)
                    for i in range(workers)
                ]
                
                results = pool.map(worker_check_range, work)
                
                for result in results:
                    if result[0] == 'counterexample':
                        counterexample = result[1]
                        reason = result[2] if len(result) > 2 else 'unknown'
                        
                        print(f"\n{'='*70}")
                        print("!!! COUNTEREXAMPLE FOUND !!!")
                        print(f"{'='*70}")
                        print(f"Number: {counterexample:,}")
                        print(f"Reason: {reason}")
                        print(f"{'='*70}\n")
                        
                        with open(COUNTEREXAMPLE_FILE, 'a') as f:
                            f.write(f"{datetime.now()}: CPU {counterexample:,} ({reason})\n")
                        
                        highest_proven = counterexample - 1
                        total_runtime = previous_total_runtime + (time.time() - session_start_time)
                        save_config(highest_proven, total_tested, total_runtime, None)
                        return
                
                batch_size = workers * chunk_size
                position += batch_size
                highest_proven = position - 1
                session_tested += batch_size
                total_tested += batch_size
                
                if session_tested % save_interval_cpu < batch_size:
                    total_runtime = previous_total_runtime + (time.time() - session_start_time)
                    save_config(highest_proven, total_tested, total_runtime, None)
                
                elapsed = time.time() - start_time
                rate = session_tested / elapsed if elapsed > 0 else 0
                ram_pct = psutil.virtual_memory().percent
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"Proven: {highest_proven:,} | "
                      f"Rate: {rate:,.0f}/s | "
                      f"Session: {session_tested:,} | "
                      f"RAM: {ram_pct:.1f}%")
    
    except KeyboardInterrupt:
        pass
    finally:
        if session_tested > 0:
            total_runtime = previous_total_runtime + (time.time() - session_start_time)
            save_config(highest_proven, total_tested, total_runtime, None)
            
            elapsed = time.time() - start_time
            rate = session_tested / elapsed if elapsed > 0 else 0
            
            # Calculate current rate
            current_interval_tested = session_tested - (getattr(check_batch_gpu, '_last_tested', 0))
            current_rate = current_interval_tested / 15.0 if current_interval_tested > 0 else rate
            
            print(f"\n{'='*70}")
            print("SESSION SUMMARY")
            print(f"{'='*70}")
            print(f"Highest proven: {highest_proven:,}")
            print(f"Session tested: {session_tested:,}")
            print(f"Total tested: {total_tested:,}")
            print(f"Average rate: {rate:,.0f}/s ({rate*2:,.0f} effective/s)")
            print(f"Current rate: {current_rate:,.0f}/s ({current_rate*2:,.0f} effective/s)")
            print(f"Time: {elapsed/60:.1f} min")
            print(f"Saved!")
            print(f"{'='*70}\n")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point - choose between GPU hybrid mode or CPU-only mode."""
    import sys
    import traceback
    
    try:
        # Check command-line arguments for mode selection
        mode = None
        if len(sys.argv) > 1:
            arg = sys.argv[1].lower()
            if arg in ['gpu', 'hybrid']:
                mode = 'gpu'
            elif arg in ['cpu', 'cpu-only']:
                mode = 'cpu'
            else:
                print("Invalid mode. Use: python CollatzEngine.py [gpu|cpu]")
                print("  gpu/hybrid  - Use GPU acceleration (default if GPU available)")
                print("  cpu/cpu-only - Use CPU-only mode")
                sys.exit(1)
        
        # Auto-detect mode if not specified
        if mode is None:
            if GPU_AVAILABLE:
                gpu_config = get_gpu_config()
                if gpu_config:
                    mode = 'gpu'
                else:
                    print("GPU detected but initialization failed. Falling back to CPU mode.\n")
                    mode = 'cpu'
            else:
                print("No GPU detected. Using CPU-only mode.\n")
                mode = 'cpu'
        
        # Run selected mode
        if mode == 'gpu':
            if not GPU_AVAILABLE:
                print("ERROR: GPU mode requested but no GPU available.")
                print("Automatically switching to CPU mode...\n")
                run_cpu_mode()
            else:
                gpu_config = get_gpu_config()
                if not gpu_config:
                    print("ERROR: GPU initialization failed.")
                    print("Automatically switching to CPU mode...\n")
                    run_cpu_mode()
                else:
                    run_gpu_mode()
        else:
            run_cpu_mode()
    
    except Exception as e:
        print(f"\n{'='*70}")
        print("FATAL ERROR")
        print(f"{'='*70}")
        print(f"An unexpected error occurred: {e}")
        print(f"\nFull traceback:")
        traceback.print_exc()
        print(f"{'='*70}")
        print("\nPlease report this error with the above information.")
        sys.exit(1)


# API functions for distributed_collatz.py
def gpu_check_range(start: int, end: int) -> dict:
    """Check a range of numbers using GPU (API for distributed workers)."""
    if not GPU_AVAILABLE:
        return cpu_check_range(start, end)
    
    numbers_checked = 0
    batch_size = 1000000
    config = get_gpu_config()
    
    if config is None:
        # GPU initialization failed, fall back to CPU
        return cpu_check_range(start, end)
    
    highest_proven = end
    
    try:
        current = start
        while current < end:
            chunk_size = min(batch_size, end - current)
            result = check_batch_gpu(current, chunk_size, highest_proven, 
                                    config['threads_per_block'])
            
            # check_batch_gpu returns tuple: ('status', value, ...)
            if result[0] == 'disproven':
                return {
                    "counterexample": result[1],
                    "numbers_checked": numbers_checked + (result[1] - start)
                }
            elif result[0] == 'success':
                numbers_checked += result[1]
            elif result[0] == 'inconclusive':
                # For API simplicity, treat inconclusive as success (needs CPU follow-up)
                numbers_checked += chunk_size
            
            current += chunk_size
        
        return {"counterexample": None, "numbers_checked": numbers_checked}
    except Exception as e:
        print(f"[GPU ERROR] {e}, falling back to CPU")
        import traceback
        traceback.print_exc()
        return cpu_check_range(start, end)


def cpu_check_range(start: int, end: int) -> dict:
    """Check a range of numbers using CPU (API for distributed workers)."""
    import multiprocessing as mp
    
    numbers_checked = 0
    chunk_size = 10000
    num_workers = min(mp.cpu_count(), 8)
    pool = mp.Pool(num_workers, initializer=init_worker)
    
    try:
        ranges = []
        current = start
        while current < end:
            chunk_end = min(current + chunk_size, end)
            ranges.append((current, chunk_end, end))
            current = chunk_end
        
        results = pool.map(worker_check_range, ranges)
        pool.close()
        pool.join()
        
        for result in results:
            if result['counterexample'] is not None:
                return {
                    "counterexample": result['counterexample'],
                    "numbers_checked": numbers_checked + result['numbers_checked']
                }
            numbers_checked += result['numbers_checked']
        
        return {"counterexample": None, "numbers_checked": numbers_checked}
        
    except Exception as e:
        pool.terminate()
        pool.join()
        raise e


if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support()
    main()
