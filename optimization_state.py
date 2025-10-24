"""
Optimization State Tracker
Tracks whether auto-tuner has completed optimization for current hardware
and detects hardware changes that require re-optimization

Copyright (c) 2025 Jay (CollatzEngine)
Licensed under CC BY-NC-SA 4.0
https://creativecommons.org/licenses/by-nc-sa/4.0/
"""

import json
import os
import hashlib
from datetime import datetime

try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

STATE_FILE = "optimization_state.json"

def get_hardware_fingerprint():
    """Generate a unique fingerprint for current hardware configuration."""
    fingerprint_data = {}
    
    if GPU_AVAILABLE:
        try:
            device = cp.cuda.Device()
            props = cp.cuda.runtime.getDeviceProperties(device.id)
            mem_info = device.mem_info
            
            fingerprint_data['gpu'] = {
                'name': props['name'].decode() if isinstance(props['name'], bytes) else props['name'],
                'vram_gb': round(mem_info[1] / (1024**3), 1),
                'compute_capability': f"{props['major']}.{props['minor']}",
                'multiprocessor_count': props['multiProcessorCount'],
            }
        except:
            fingerprint_data['gpu'] = None
    else:
        fingerprint_data['gpu'] = None
    
    # CPU info
    import platform
    fingerprint_data['cpu'] = {
        'processor': platform.processor(),
        'cpu_count': os.cpu_count(),
    }
    
    # Create hash of fingerprint
    fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
    fingerprint_hash = hashlib.sha256(fingerprint_str.encode()).hexdigest()
    
    return fingerprint_hash, fingerprint_data

def load_optimization_state():
    """Load optimization state from file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def save_optimization_state(optimized=False, benchmark_completed=False):
    """Save optimization state."""
    fingerprint_hash, fingerprint_data = get_hardware_fingerprint()
    
    state = {
        'hardware_fingerprint': fingerprint_hash,
        'hardware_details': fingerprint_data,
        'optimized': optimized,
        'benchmark_completed': benchmark_completed,
        'last_updated': datetime.now().isoformat(),
    }
    
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    
    return state

def needs_optimization():
    """
    Check if optimization is needed.
    Returns (needs_opt, reason, state)
    - needs_opt: bool - whether optimization should run
    - reason: str - explanation
    - state: dict - current state
    """
    current_fingerprint, current_hardware = get_hardware_fingerprint()
    state = load_optimization_state()
    
    # Check if gpu_tuning.json exists (indicates previous tuning)
    gpu_tuning_exists = os.path.exists('gpu_tuning.json')
    
    # First run - no state file
    if state is None:
        # But if gpu_tuning.json exists, create state from it
        if gpu_tuning_exists:
            print("[OPTIMIZATION STATE] Found existing gpu_tuning.json, creating state...")
            save_optimization_state(optimized=True, benchmark_completed=False)
            return False, "Using existing GPU tuning configuration", None
        return True, "First run - no optimization state found", None
    
    # Hardware changed
    if state.get('hardware_fingerprint') != current_fingerprint:
        return True, "Hardware configuration changed since last optimization", state
    
    # Optimization was interrupted/not completed
    if not state.get('optimized', False):
        # But check if gpu_tuning.json exists as fallback
        if gpu_tuning_exists:
            print("[OPTIMIZATION STATE] Marking as optimized based on existing tuning file...")
            save_optimization_state(optimized=True, benchmark_completed=False)
            return False, "Restored optimization state from existing tuning", state
        return True, "Previous optimization did not complete", state
    
    # Already optimized for this hardware
    return False, "System already optimized for current hardware", state

def needs_benchmark():
    """Check if final benchmark is needed after optimization."""
    state = load_optimization_state()
    
    if state is None:
        return False
    
    # If optimized but benchmark not yet run
    if state.get('optimized', False) and not state.get('benchmark_completed', False):
        return True
    
    return False

def mark_optimization_complete():
    """Mark that optimization has completed successfully."""
    save_optimization_state(optimized=True, benchmark_completed=False)
    print("\n[OPTIMIZATION STATE] Optimization completed and saved")

def mark_benchmark_complete():
    """Mark that final benchmark has been completed."""
    state = load_optimization_state()
    if state:
        save_optimization_state(optimized=True, benchmark_completed=True)
        print("\n[OPTIMIZATION STATE] Benchmark completed and saved")

def get_optimization_status():
    """Get human-readable optimization status."""
    needs_opt, reason, state = needs_optimization()
    
    # If needs_opt is False, system is already optimized
    if not needs_opt:
        if needs_benchmark():
            return {
                'needs_optimization': False,
                'status': 'optimized_awaiting_benchmark',
                'reason': 'Optimization complete, final benchmark pending',
                'benchmark_ready': True
            }
        return {
            'needs_optimization': False,
            'status': 'fully_optimized',
            'reason': reason,
            'benchmark_ready': False
        }
    
    # Needs optimization
    if state is None:
        return {
            'needs_optimization': True,
            'status': 'unoptimized',
            'reason': reason,
            'benchmark_ready': False
        }
    
    return {
        'needs_optimization': True,
        'status': 'needs_reoptimization',
        'reason': reason,
        'benchmark_ready': False
    }

def is_system_optimized():
    """Simple check: is system currently optimized?"""
    state = load_optimization_state()
    if state is None:
        return False
    
    current_fingerprint, _ = get_hardware_fingerprint()
    
    # Must match hardware and be marked as optimized
    return (state.get('hardware_fingerprint') == current_fingerprint and 
            state.get('optimized', False))
