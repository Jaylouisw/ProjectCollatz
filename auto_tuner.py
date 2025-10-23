"""
Auto-tuner for Collatz GPU Performance
Uses adaptive search to find optimal GPU settings quickly
Automatically detects and tunes for any GPU hardware
"""

import json
import time
import os
from datetime import datetime
import itertools

try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    cp = None

def detect_gpu_ranges():
    """Detect GPU capabilities and set appropriate tuning ranges.
    Future-proofed for 100 years following Moore's Law trends."""
    if not GPU_AVAILABLE:
        print("ERROR: GPU not available. Cannot run auto-tuner.")
        exit(1)
    
    device = cp.cuda.Device()
    props = cp.cuda.runtime.getDeviceProperties(device.id)
    mem_info = device.mem_info
    
    vram_gb = mem_info[1] / (1024**3)
    sm_count = props['multiProcessorCount']
    
    print(f"Detected GPU: {props['name'].decode()}")
    print(f"VRAM: {vram_gb:.1f} GB")
    print(f"Streaming Multiprocessors: {sm_count}")
    print()
    
    # VRAM-based scaling (future-proofed for terabytes+)
    if vram_gb < 3:
        # Low VRAM (2GB) - legacy hardware
        batch_sizes = [5_000_000, 8_000_000, 10_000_000, 12_000_000, 15_000_000]
        max_mem = 60
    elif vram_gb < 5:
        # Medium VRAM (4GB) - 2020s entry level
        batch_sizes = [15_000_000, 18_000_000, 20_000_000, 22_000_000, 25_000_000, 28_000_000, 30_000_000, 35_000_000, 40_000_000]
        max_mem = 80
    elif vram_gb < 9:
        # High VRAM (6-8GB) - 2020s mid-range
        batch_sizes = [30_000_000, 35_000_000, 40_000_000, 45_000_000, 50_000_000, 60_000_000, 70_000_000, 80_000_000]
        max_mem = 90
    elif vram_gb < 30:
        # Very high VRAM (10-30GB) - 2020s high-end
        batch_sizes = [50_000_000, 60_000_000, 70_000_000, 80_000_000, 100_000_000, 120_000_000, 150_000_000]
        max_mem = 95
    elif vram_gb < 100:
        # Extreme VRAM (30-100GB) - 2020s-2030s datacenter
        batch_sizes = [100_000_000, 150_000_000, 200_000_000, 250_000_000, 300_000_000, 400_000_000, 500_000_000]
        max_mem = 95
    elif vram_gb < 1000:
        # Massive VRAM (100GB-1TB) - 2030s-2060s expected
        # Scale batch sizes proportionally to VRAM
        base = int(vram_gb * 5_000_000)  # 5M per GB baseline
        batch_sizes = [base, int(base*1.2), int(base*1.5), int(base*2), int(base*2.5), int(base*3)]
        max_mem = 95
    else:
        # Future VRAM (1TB+) - 2060s+ theoretical
        # Use percentage-based allocation to prevent overflow
        base = 1_000_000_000  # 1 billion baseline
        batch_sizes = [base, int(base*1.5), int(base*2), int(base*3), int(base*4), int(base*5)]
        max_mem = 95
    
    # SM count-based scaling (future-proofed for massive parallelism)
    if sm_count < 10:
        # Low-end GPU - legacy
        thread_mults = [4, 6, 8, 10]
        work_mults = [400, 600, 800, 1000]
        blocks_per_sm = [2, 3, 4]
    elif sm_count < 30:
        # Mid-range GPU (like RTX 3050) - 2020s
        thread_mults = [6, 8, 10, 12, 14, 16]
        work_mults = [700, 800, 850, 900, 950, 1000, 1100, 1200]
        blocks_per_sm = [2, 3, 4, 5, 6]
    elif sm_count < 70:
        # High-end GPU (like RTX 3080) - 2020s
        thread_mults = [8, 10, 12, 14, 16, 20]
        work_mults = [1000, 1200, 1400, 1600, 1800, 2000]
        blocks_per_sm = [4, 5, 6, 7, 8]
    elif sm_count < 150:
        # Extreme GPU (like RTX 4090, H100) - 2020s-2030s
        thread_mults = [12, 16, 20, 24, 32]
        work_mults = [1500, 2000, 2500, 3000, 3500, 4000]
        blocks_per_sm = [6, 8, 10, 12]
    elif sm_count < 500:
        # Next-gen datacenter (150-500 SMs) - 2030s-2050s
        thread_mults = [16, 20, 24, 32, 40, 48]
        work_mults = [3000, 4000, 5000, 6000, 8000, 10000]
        blocks_per_sm = [8, 10, 12, 16]
    elif sm_count < 2000:
        # Advanced future GPU (500-2000 SMs) - 2050s-2080s
        thread_mults = [24, 32, 40, 48, 64]
        work_mults = [8000, 10000, 12000, 15000, 20000]
        blocks_per_sm = [12, 16, 20, 24]
    else:
        # Far future / theoretical (2000+ SMs) - 2080s-2125+
        # Scale parameters based on SM count
        base_thread = max(32, min(128, sm_count // 40))
        thread_mults = [base_thread, int(base_thread*1.5), int(base_thread*2), int(base_thread*3)]
        base_work = max(10000, min(100000, sm_count * 10))
        work_mults = [base_work, int(base_work*1.2), int(base_work*1.5), int(base_work*2)]
        blocks_per_sm = [16, 20, 24, 32]
    
    # Memory percentage options for testing
    mem_percents = list(range(5, max_mem + 1, 5))  # 5%, 10%, 15%, ... up to max_mem
    
    return {
        'batch_sizes': batch_sizes,
        'thread_multipliers': thread_mults,
        'work_multipliers': work_mults,
        'blocks_per_sm': blocks_per_sm,
        'memory_percents': mem_percents,
        'vram_gb': vram_gb,
        'sm_count': sm_count
    }

TEST_DURATION = 120  # Seconds per configuration test (2 minutes - faster tuning)
QUICK_TEST_DURATION = 60  # Quick test for early elimination (1 minute)
CONFIG_FILE = "collatz_config.json"
TUNING_FILE = "gpu_tuning.json"
LOG_FILE = "tuning_log.txt"
STATE_FILE = "autotuner_state.json"

def save_state(stage, iteration, best_rate, best_config, baseline, cycles_without_improvement=0):
    """Save auto-tuner state for resume capability."""
    state = {
        'stage': stage,
        'iteration': iteration,
        'best_rate': best_rate,
        'best_config': best_config,
        'baseline': baseline,
        'cycles_without_improvement': cycles_without_improvement,
        'timestamp': datetime.now().isoformat()
    }
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def load_state():
    """Load auto-tuner state if exists."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def clear_state():
    """Clear saved state."""
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

def load_tuning():
    """Load current GPU tuning config."""
    with open(TUNING_FILE, 'r') as f:
        return json.load(f)

def save_tuning(config):
    """Save GPU tuning config."""
    with open(TUNING_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Applied: {config}")

def get_test_rate(duration=120, quick_test=False):
    """Monitor for specified duration and return AVERAGE rate over multiple samples.
    If quick_test=True, fail fast on crashes."""
    if not os.path.exists(CONFIG_FILE):
        print(" [ERROR: Config file not found]", end='')
        return 0
    
    # Adaptive sampling: shorter intervals for quick tests
    if quick_test or duration <= 60:
        sample_interval = 15  # 15 seconds for quick tests
        max_failures = 2  # Fail fast
    else:
        sample_interval = 20  # 20 seconds for normal tests (faster than 30s)
        max_failures = 3
    
    num_samples = max(2, duration // sample_interval)  # At least 2 samples
    
    samples = []
    failed_samples = 0
    
    print(f"\n  Taking {num_samples} samples over {duration}s...", flush=True)
    
    for i in range(num_samples):
        # Read initial state for this sample
        try:
            with open(CONFIG_FILE, 'r') as f:
                initial = json.load(f)
            initial_tested = initial.get('total_tested', 0)
        except:
            print(f"\n  [ERROR: Cannot read config at sample {i+1}]", end='')
            continue
        
        # Wait for sample interval
        time.sleep(sample_interval)
        
        # Read final state for this sample
        try:
            with open(CONFIG_FILE, 'r') as f:
                final = json.load(f)
            final_tested = final.get('total_tested', 0)
        except:
            print(f"\n  [ERROR: Cannot read config at sample {i+1}]", end='')
            continue
        
        tested = final_tested - initial_tested
        
        # If no progress, the checker probably crashed
        if tested == 0:
            failed_samples += 1
            print(f"\n  [Sample {i+1}/{num_samples}: No progress - failure {failed_samples}/{max_failures}]", end='', flush=True)
            # Fail fast on quick tests or after max failures
            if failed_samples >= max_failures:
                print(f"\n  [FAILED: {max_failures} samples with no progress - aborting]", end='')
                return 0
            continue
        
        # Reset failure counter on successful sample
        failed_samples = 0
        sample_rate = tested / sample_interval
        samples.append(sample_rate)
        
        # Show progress with better formatting
    print(f"\n  Sample {i+1}/{num_samples}: {sample_rate:,.0f} odd/s", end='', flush=True)
        
        # Early success detection for quick tests
        if quick_test and len(samples) >= 2:
            # If we have 2 good samples in quick test, that's enough
            avg_so_far = sum(samples) / len(samples)
            if avg_so_far > 0:
                print(f"\n  [Quick test passed - avg {avg_so_far:,.0f} odd/s]", end='')
                return avg_so_far
    
    # If no valid samples, config is broken
    if not samples:
        print("\n  [FAILED: No valid samples]", end='')
        return 0
    
    # Calculate average, min, max
    avg_rate = sum(samples) / len(samples)
    min_rate = min(samples)
    max_rate = max(samples)
    
    # Calculate standard deviation
    if len(samples) > 1:
        variance = sum((x - avg_rate) ** 2 for x in samples) / len(samples)
        std_dev = variance ** 0.5
        cv = (std_dev / avg_rate * 100) if avg_rate > 0 else 0  # Coefficient of variation (%)
    else:
        std_dev = 0
        cv = 0
    
    print(f"\n  Average: {avg_rate:,.0f} odd/s | Min: {min_rate:,.0f} | Max: {max_rate:,.0f} | StdDev: {std_dev:,.0f} ({cv:.1f}%)", end='')
    
    return avg_rate

def log_result(config, rate):
    """Log tuning result."""
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] Rate: {rate:,.0f}/s | Config: {config}\n")

def test_config(batch, thread_mult, work_mult, blocks_sm, iteration, total, test_duration=120, quick_test=False):
    """Test a single configuration and return its rate.
    If quick_test=True, does a 60s quick validation first."""
    test_config = {
        "work_multiplier": work_mult,
        "threads_per_block_multiplier": thread_mult,
        "blocks_per_sm": blocks_sm,
        "batch_size_override": batch
    }
    
    test_label = "QUICK" if quick_test else "FULL"
    print(f"\n[{iteration}/{total}] {test_label} Testing ({test_duration}s):")
    print(f"  Batch: {batch:,} | Threads: {thread_mult} | Work: {work_mult} | Blocks/SM: {blocks_sm}")
    
    save_tuning(test_config)
    time.sleep(8)  # Reduced from 12s - wait for config reload
    
    print(f"  Measuring for {test_duration}s...", end='', flush=True)
    rate = get_test_rate(test_duration, quick_test)
    
    if rate > 0:
    print(f" [OK] {rate:,.0f} odd/s")
    else:
        print(f" [FAILED] - Config causes crash/hang")
    
    log_result(test_config, rate)
    
    return rate, test_config

def binary_search_param(param_name, param_list, baseline_config, iteration_offset=0):
    """Use binary search to find optimal value for a single parameter.
    Much faster than linear sweep."""
    print(f"\n[SEARCH] Binary searching {param_name.upper()}...")
    
    best_rate = 0
    best_value = baseline_config[param_name]
    
    left = 0
    right = len(param_list) - 1
    tests_done = 0
    
    while left <= right:
        mid = (left + right) // 2
        value = param_list[mid]
        
        # Skip if we already tested this exact value
        if value == best_value and best_rate > 0:
            break
        
        # Build test config
        config = baseline_config.copy()
        config[param_name] = value
        
        tests_done += 1
        
        # Quick test first (60s)
        rate, _ = test_config(
            config['batch'], config['thread'], config['work'], config['blocks'],
            iteration_offset + tests_done, "binary", QUICK_TEST_DURATION, quick_test=True
        )
        
        if rate > best_rate:
            best_rate = rate
            best_value = value
            print(f"  [NEW BEST] {rate:,.0f} odd/s")
            # Search higher values
            left = mid + 1
        else:
            # Search lower values
            right = mid - 1
    
    print(f"  -> Binary search complete: {param_name}={best_value} ({best_rate:,.0f} odd/s) in {tests_done} tests")
    baseline_config[param_name] = best_value
    return best_rate, best_value
    save_tuning(test_config)
    time.sleep(12)  # Wait for config reload
    
    print(f"  Measuring for {test_duration}s...", end='', flush=True)
    rate = get_test_rate(test_duration)
    
    if rate > 0:
    print(f" {rate:,.0f} odd/s")
    else:
        print(f" FAILED - Config causes crash/hang")
    
    log_result(test_config, rate)
    
    return rate, test_config

def adaptive_search():
    """Multi-stage adaptive search to find optimal settings quickly."""
    
    # Check for resume state
    saved_state = load_state()
    
    if saved_state:
        print("=" * 70)
        print("RESUMING AUTO-TUNER FROM SAVED STATE")
        print("=" * 70)
        print(f"Previous session: {saved_state['timestamp']}")
        print(f"Stage: {saved_state['stage']}")
        print(f"Best rate: {saved_state['best_rate']:,.0f} odd/s")
        print("=" * 70)
        response = input("\nResume from saved state? (y/n): ").lower()
        if response != 'y':
            print("Starting fresh...")
            clear_state()
            saved_state = None
        else:
            print("Resuming...")
    
    print("=" * 70)
    print("COLLATZ ADAPTIVE AUTO-TUNER - FAST MODE")
    print("=" * 70)
    print("Stage 1: Binary search (60s quick tests)")
    print("Stage 2: Fine-tune top configs (2 min tests)")
    print("Stage 3: Progressive refinement (2 min -> 1 min tests)")
    print("Optimizations: Fast sampling, early termination, binary search")
    print("=" * 70)
    print()
    
    # Detect GPU and get appropriate tuning ranges
    gpu_ranges = detect_gpu_ranges()
    
    BATCH_SIZES = gpu_ranges['batch_sizes']
    THREAD_MULTIPLIERS = gpu_ranges['thread_multipliers']
    WORK_MULTIPLIERS = gpu_ranges['work_multipliers']
    MEMORY_PERCENTS = gpu_ranges['memory_percents']
    BLOCKS_PER_SM = gpu_ranges['blocks_per_sm']
    
    print(f"Tuning ranges for this GPU:")
    print(f"  Batch sizes: {len(BATCH_SIZES)} options ({BATCH_SIZES[0]:,} to {BATCH_SIZES[-1]:,})")
    print(f"  Thread multipliers: {len(THREAD_MULTIPLIERS)} options ({THREAD_MULTIPLIERS[0]} to {THREAD_MULTIPLIERS[-1]})")
    print(f"  Work multipliers: {len(WORK_MULTIPLIERS)} options ({WORK_MULTIPLIERS[0]} to {WORK_MULTIPLIERS[-1]})")
    print(f"  Memory usage: {len(MEMORY_PERCENTS)} options (5% to {MEMORY_PERCENTS[-1]}%)")
    print(f"  Blocks per SM: {len(BLOCKS_PER_SM)} options ({BLOCKS_PER_SM[0]} to {BLOCKS_PER_SM[-1]})")
    print()
    
    # Initialize or resume state
    if saved_state:
        best_rate = saved_state['best_rate']
        best_config = saved_state['best_config']
        baseline = saved_state['baseline']
        iteration = saved_state['iteration']
        current_stage = saved_state['stage']
        cycles_without_improvement = saved_state.get('cycles_without_improvement', 0)
        refinement_level = saved_state.get('refinement_level', 1.0)
        print(f"[RESUME] Resuming from stage {current_stage}, iteration {iteration}")
    print(f"   Best rate so far: {best_rate:,.0f} odd/s")
        if current_stage == 3:
            print(f"   Refinement level: {refinement_level:.3f}")
        print()
    else:
        best_rate = 0
        best_config = None
        baseline = {
            'batch': BATCH_SIZES[len(BATCH_SIZES)//2],
            'thread': THREAD_MULTIPLIERS[len(THREAD_MULTIPLIERS)//2],
            'work': WORK_MULTIPLIERS[len(WORK_MULTIPLIERS)//2],
            'blocks': BLOCKS_PER_SM[len(BLOCKS_PER_SM)//2]
        }
        iteration = 0
        current_stage = 1
        cycles_without_improvement = 0
        refinement_level = 1.0
    
    # Stage 1: Binary search for each parameter (much faster than linear sweep)
    if current_stage <= 1:
        print("\n### STAGE 1: Binary Search for Optimal Parameters ###\n")
        print("Note: No VRAM limits applied - testing full parameter space\n")
        
        # Use binary search for each parameter - WAY faster!
        best_rate, best_batch = binary_search_param('batch', BATCH_SIZES, baseline, iteration)
        iteration += 5  # Approximate iterations used
        
        best_rate, best_thread = binary_search_param('thread', THREAD_MULTIPLIERS, baseline, iteration)
        iteration += 5
        
        best_rate, best_work = binary_search_param('work', WORK_MULTIPLIERS, baseline, iteration)
        iteration += 5
        
        best_rate, best_blocks = binary_search_param('blocks', BLOCKS_PER_SM, baseline, iteration)
        iteration += 5
        
        # Build best config
        best_config = {
            "work_multiplier": best_work,
            "threads_per_block_multiplier": best_thread,
            "blocks_per_sm": best_blocks,
            "batch_size_override": best_batch
        }
        
    print(f"\n[STAGE 1 COMPLETE] Best rate: {best_rate:,.0f} odd/s")
        print(f"   Config: batch={best_batch:,}, thread={best_thread}, work={best_work}, blocks={best_blocks}")
        
        # Mark stage 1 complete
        current_stage = 2
        save_state(2, iteration, best_rate, best_config, baseline, 0)
    else:
        # Resuming from stage 2 or 3 - extract best values
        best_batch = best_config['batch_size_override']
        best_thread = best_config['threads_per_block_multiplier']
        best_work = best_config['work_multiplier']
        best_blocks = best_config['blocks_per_sm']
    
    # Stage 2: Fine-tune around best values (skip if already completed)
    if current_stage <= 2:
        print("\n### STAGE 2: Fine-Tuning ###\n")
        
        # Create narrow ranges around best values
        batch_idx = BATCH_SIZES.index(best_batch) if best_batch in BATCH_SIZES else len(BATCH_SIZES)//2
        batch_fine = [BATCH_SIZES[max(0, batch_idx-1)], best_batch, 
                      BATCH_SIZES[min(len(BATCH_SIZES)-1, batch_idx+1)]] if batch_idx > 0 else [best_batch]
        
        work_idx = WORK_MULTIPLIERS.index(best_work) if best_work in WORK_MULTIPLIERS else len(WORK_MULTIPLIERS)//2
        work_fine = [WORK_MULTIPLIERS[max(0, work_idx-1)], best_work,
                     WORK_MULTIPLIERS[min(len(WORK_MULTIPLIERS)-1, work_idx+1)]] if work_idx > 0 else [best_work]
        
        # Test combinations of top parameters
        for batch, work in itertools.product(set(batch_fine), set(work_fine)):
            iteration += 1
            rate, config = test_config(batch, best_thread, work, best_blocks, iteration, "inf", TEST_DURATION)
            if rate > best_rate:
                best_rate = rate
                best_config = config
                print(f"  *** NEW BEST: {rate:,.0f} odd/s ***")
            save_state(2, iteration, best_rate, best_config, baseline, 0)
        
        # Mark stage 2 complete
        current_stage = 3
        save_state(3, iteration, best_rate, best_config, baseline, 0)
        
        # Update best values for stage 3
        best_batch = best_config['batch_size_override']
        best_thread = best_config['threads_per_block_multiplier']
        best_work = best_config['work_multiplier']
        best_blocks = best_config['blocks_per_sm']
    
    print("\n" + "=" * 70)
    print("STAGE 1 & 2 COMPLETE - ENTERING PROGRESSIVE REFINEMENT")
    print("=" * 70)
    print(f"Current best rate: {best_rate:,.0f} odd/s")
    print(f"\nOptimal Configuration:")
    for key, value in best_config.items():
        print(f"  {key}: {value:,}" if isinstance(value, int) else f"  {key}: {value}")
    print("=" * 70)
    
    # Stage 3: Progressive refinement with logarithmic convergence
    print("\n### STAGE 3: Progressive Refinement ###\n")
    print("Starting with large adjustments, reducing on curve until peak found")
    print("Press Ctrl+C to stop\n")
    
    # Extract best values
    best_batch = best_config['batch_size_override']
    best_thread = best_config['threads_per_block_multiplier']
    best_work = best_config['work_multiplier']
    best_blocks = best_config['blocks_per_sm']
    
    cycles_without_improvement = 0
    max_cycles_without_improvement = 30
    cycle = 0
    refinement_level = 1.0  # Start at 100% of base adjustments
    
    while refinement_level > 0.01:  # Stop when adjustments < 1% of original
        cycle += 1
        cycle_improved = False
        
        # Calculate scaled adjustments based on refinement level
        batch_adj = int(2_000_000 * refinement_level)  # 2M -> 20K
        work_adj = int(50 * refinement_level)          # 50 -> 0.5
        thread_adj = max(1, int(2 * refinement_level)) # 2 -> 1
        
        # Calculate adaptive test duration (reduces as we converge)
        test_duration = max(120, int(TEST_DURATION * refinement_level))  # 120s minimum
        
        print(f"\n[Cycle {cycle}] Refinement: {refinement_level:.3f} | Test: {test_duration}s | Adjustments: +/-{batch_adj:,} batch, +/-{work_adj} work")
        print(f"  No improvement: {cycles_without_improvement}/{max_cycles_without_improvement} cycles")
        
        iteration += 1
        
        # Generate variations scaled by refinement level (no memory param)
        test_variations = [
            # Batch variations
            (best_batch + batch_adj, best_thread, best_work, best_blocks),
            (best_batch - batch_adj, best_thread, best_work, best_blocks),
            (best_batch + batch_adj//2, best_thread, best_work, best_blocks),
            (best_batch - batch_adj//2, best_thread, best_work, best_blocks),
            # Work variations
            (best_batch, best_thread, best_work + work_adj, best_blocks),
            (best_batch, best_thread, best_work - work_adj, best_blocks),
            (best_batch, best_thread, best_work + work_adj//2, best_blocks),
            (best_batch, best_thread, best_work - work_adj//2, best_blocks),
            # Thread variations
            (best_batch, best_thread + thread_adj, best_work, best_blocks),
            (best_batch, best_thread - thread_adj, best_work, best_blocks),
            # Blocks variations
            (best_batch, best_thread, best_work, best_blocks + 1),
            (best_batch, best_thread, best_work, best_blocks - 1),
            # Combined variations
            (best_batch + batch_adj, best_thread, best_work + work_adj, best_blocks),
            (best_batch - batch_adj, best_thread, best_work - work_adj, best_blocks),
            (best_batch + batch_adj//2, best_thread + thread_adj, best_work, best_blocks),
            (best_batch - batch_adj//2, best_thread - thread_adj, best_work, best_blocks),
            (best_batch, best_thread + thread_adj, best_work + work_adj, best_blocks),
            (best_batch, best_thread - thread_adj, best_work - work_adj, best_blocks),
        ]
        
        # Test each variation
        for batch, thread, work, blocks in test_variations:
            # Skip invalid values
            if batch < 5_000_000 or batch > 200_000_000:
                continue
            if thread < 4 or thread > 20:
                continue
            if work < 500 or work > 2000:
                continue
            if blocks < 1 or blocks > 12:
                continue
            
            iteration += 1
            rate, config = test_config(batch, thread, work, blocks, iteration, "inf", test_duration)
            if rate > best_rate:
                old_rate = best_rate
                best_rate = rate
                best_config = config
                best_batch = batch
                best_thread = thread
                best_work = work
                best_blocks = blocks
                cycle_improved = True
                improvement_pct = ((rate - old_rate) / old_rate * 100) if old_rate > 0 else 0
                print(f"  [NEW PEAK] {rate:,.0f} odd/s [+{improvement_pct:.2f}%]")
                print(f"     Config: Batch={batch:,}, Thread={thread}, Work={work}, Blocks={blocks}")
                
                # Reset refinement level when improvement found (explore neighborhood)
                refinement_level = 1.0
                cycles_without_improvement = 0
                print(f"  [RESET] Refinement reset to 1.0 - exploring new neighborhood")
                break  # Start fresh cycle with new best
        
        if cycle_improved:
            # Save improved state
            save_state(3, iteration, best_rate, best_config, baseline, 0)
        else:
            # Reduce refinement level (exponential decay)
            refinement_level *= 0.95
            cycles_without_improvement += 1
            
            # Save state
            save_state(3, iteration, best_rate, best_config, baseline, cycles_without_improvement)
        
        # Status report
    print(f"\n  Current peak: {best_rate:,.0f} odd/s")
        print(f"  Best config: Batch={best_batch:,}, Thread={best_thread}, Work={best_work}, Blocks={best_blocks}")
        
        # Check for convergence
        if cycles_without_improvement >= max_cycles_without_improvement:
            print(f"\n[CONVERGED] Peak performance reached ({max_cycles_without_improvement} cycles without improvement)")
            break
    
    if refinement_level <= 0.01:
        print(f"\n[CONVERGED] True convergence reached (adjustments < 1% of original)")
    
    print("\n" + "=" * 70)
    print("AUTO-TUNING COMPLETE - PEAK PERFORMANCE FOUND")
    print("=" * 70)
    print(f"Final peak rate: {best_rate:,.0f} odd/s")
    print(f"\nOptimal Configuration:")
    for key, value in best_config.items():
        print(f"  {key}: {value:,}" if isinstance(value, int) else f"  {key}: {value}")
    print("=" * 70)
    
    return best_config

def main():
    try:
        best_config = adaptive_search()
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("AUTO-TUNER STOPPED BY USER")
        print("=" * 70)
        print("Best configuration has been applied and is running.")
        print("Check tuning_log.txt for all results.")
        print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAuto-tuner stopped by user.")
