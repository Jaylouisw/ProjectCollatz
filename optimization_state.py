"""
Optimization State Management
Tracks system optimization status and hardware fingerprinting

Copyright (c) 2025 Jay (CollatzEngine)
Licensed under CC BY-NC-SA 4.0
https://creativecommons.org/licenses/by-nc-sa/4.0/
"""

import json
import os
import hashlib
import platform
from datetime import datetime

STATE_FILE = "optimization_state.json"

def get_hardware_fingerprint():
    """Generate a hardware fingerprint to detect changes."""
    try:
        # Import here to avoid circular dependency
        import cupy as cp
        
        # Get GPU info
        gpu_info = []
        try:
            device_count = cp.cuda.runtime.getDeviceCount()
            for i in range(device_count):
                with cp.cuda.Device(i):
                    props = cp.cuda.runtime.getDeviceProperties(i)
                    gpu_info.append({
                        'name': props['name'].decode(),
                        'memory': props['totalGlobalMem'],
                        'compute': f"{props['major']}.{props['minor']}"
                    })
        except:
            gpu_info = []
            
        # System info
        system_info = {
            'platform': platform.platform(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'gpus': gpu_info
        }
        
    except ImportError:
        # No GPU available
        system_info = {
            'platform': platform.platform(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'gpus': []
        }
    
    # Create fingerprint hash
    info_str = json.dumps(system_info, sort_keys=True)
    return hashlib.sha256(info_str.encode()).hexdigest()[:16]

def load_state():
    """Load optimization state from file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    # Return default state
    return {
        'hardware_fingerprint': None,
        'optimization_complete': False,
        'benchmark_complete': False,
        'last_updated': None,
        'version': '1.0'
    }

def save_state(state):
    """Save optimization state to file."""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except IOError:
        pass  # Fail silently if we can't save

def get_optimization_status():
    """Get current optimization status with reason."""
    state = load_state()
    current_fingerprint = get_hardware_fingerprint()
    
    if state['hardware_fingerprint'] is None:
        return {
            'status': 'never_optimized',
            'reason': 'Never optimized',
            'needs_optimization': True
        }
    
    if state['hardware_fingerprint'] != current_fingerprint:
        return {
            'status': 'hardware_changed',
            'reason': 'Hardware changed',
            'needs_optimization': True
        }
    
    if not state['optimization_complete']:
        return {
            'status': 'incomplete',
            'reason': 'Optimization incomplete',
            'needs_optimization': True
        }
    
    return {
        'status': 'optimized',
        'reason': 'Hardware unchanged',
        'needs_optimization': False
    }

def is_system_optimized():
    """Check if system is optimized for current hardware."""
    status = get_optimization_status()
    return not status['needs_optimization']

def mark_optimization_complete():
    """Mark optimization as complete for current hardware."""
    state = load_state()
    state['hardware_fingerprint'] = get_hardware_fingerprint()
    state['optimization_complete'] = True
    state['last_updated'] = datetime.now().isoformat()
    save_state(state)

def mark_benchmark_complete():
    """Mark benchmark as complete."""
    state = load_state()
    state['benchmark_complete'] = True
    state['last_updated'] = datetime.now().isoformat()
    save_state(state)

def reset_optimization_state():
    """Reset optimization state (force re-optimization)."""
    state = load_state()
    state['hardware_fingerprint'] = None
    state['optimization_complete'] = False
    state['benchmark_complete'] = False
    state['last_updated'] = datetime.now().isoformat()
    save_state(state)

def get_detailed_status():
    """Get detailed status information."""
    state = load_state()
    current_fingerprint = get_hardware_fingerprint()
    optimization_status = get_optimization_status()
    
    return {
        'current_hardware_fingerprint': current_fingerprint,
        'stored_hardware_fingerprint': state.get('hardware_fingerprint'),
        'optimization_complete': state.get('optimization_complete', False),
        'benchmark_complete': state.get('benchmark_complete', False),
        'last_updated': state.get('last_updated'),
        'status': optimization_status['status'],
        'reason': optimization_status['reason'],
        'needs_optimization': optimization_status['needs_optimization']
    }

# Example usage and testing
if __name__ == "__main__":
    print("Optimization State Manager")
    print("=" * 40)
    
    status = get_detailed_status()
    
    print(f"Status: {status['status']}")
    print(f"Reason: {status['reason']}")
    print(f"Needs Optimization: {status['needs_optimization']}")
    print(f"Optimization Complete: {status['optimization_complete']}")
    print(f"Benchmark Complete: {status['benchmark_complete']}")
    print(f"Last Updated: {status['last_updated']}")
    print()
    print(f"Current Hardware Fingerprint: {status['current_hardware_fingerprint']}")
    print(f"Stored Hardware Fingerprint: {status['stored_hardware_fingerprint']}")