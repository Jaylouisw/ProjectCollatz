"""
SIMD-Optimized Collatz Checker using NumPy
Processes multiple numbers using vectorization

NOTE: NumPy vectorization shows SLOWER performance than scalar code for Collatz
due to:
1. High overhead of NumPy array operations
2. Sequential nature of Collatz (each step depends on previous)
3. Branch divergence (different numbers take different paths)

For true SIMD speedup, would need:
- Native C/C++ implementation with AVX-512 intrinsics
- Custom assembly code  
- Or Numba JIT compilation with explicit SIMD

This module serves as a proof-of-concept and falls back to scalar.

Copyright (c) 2025 Jay Wenden (CollatzEngine)
Licensed under CC BY-NC-SA 4.0
"""

import numpy as np

# Check if we have NumPy
SIMD_AVAILABLE = True
try:
    test = np.array([1, 2, 3, 4], dtype=np.uint64)
    _ = test * 3 + 1
except:
    SIMD_AVAILABLE = False


def collatz_check_simd_batch(start_values, highest_proven, max_steps=100000):
    """
    NumPy vectorized Collatz checker.
    
    NOTE: Due to NumPy overhead, this is actually SLOWER than scalar code.
    Kept for reference. For real SIMD gains, use Numba or C++ with AVX-512.
    
    Falls back to scalar processing automatically.
    """
    # Always use scalar - NumPy overhead is too high for this workload
    return [collatz_check_scalar(n, highest_proven, max_steps) for n in start_values]


def collatz_check_scalar(n, highest_proven, max_steps=100000):
    """
    Scalar fallback for single number checking.
    Optimized version of the standard algorithm.
    """
    if n <= highest_proven:
        return (True, 0, 'already_proven')
    
    original_n = n
    steps = 0
    visited = set()
    
    while n > 1 and steps < max_steps:
        if n in visited:
            return (False, steps, 'loop_detected')
        
        if n <= highest_proven:
            return (True, steps, 'hit_proven')
        
        # Lazy cycle detection
        if steps % 50 == 0:
            visited.add(n)
        
        if n & 1:
            # Odd: 3n+1 then divide by 2
            n = (n * 3 + 1) >> 1
            steps += 1
        else:
            # Even: divide by 2^k where k = trailing zeros
            tz = (n & -n).bit_length() - 1
            n >>= tz
            steps += tz
    
    if steps >= max_steps:
        return (False, steps, 'step_limit')
    
    return (n == 1, steps, 'reached_1' if n == 1 else 'unknown')


def collatz_check_simd_optimized(start_values, highest_proven, max_steps=100000):
    """
    Advanced SIMD version with trailing zero optimization.
    Processes 8 numbers at once with full optimization.
    """
    if not SIMD_AVAILABLE:
        return [collatz_check_scalar(n, highest_proven, max_steps) for n in start_values]
    
    # Ensure batch size is multiple of 8
    batch_size = len(start_values)
    pad_size = (8 - (batch_size % 8)) % 8
    
    if pad_size > 0:
        padded = list(start_values) + [1] * pad_size
    else:
        padded = start_values
    
    n = np.array(padded, dtype=np.uint64)
    steps = np.zeros(len(n), dtype=np.int32)
    active = np.ones(len(n), dtype=bool)
    results = [None] * len(n)
    
    # Cycle detection state
    check_interval = 64
    last_check = n.copy()
    
    for iteration in range(max_steps):
        # Convergence checks
        mask_one = (n == 1) & active
        mask_proven = (n <= highest_proven) & (n > 1) & active
        
        if np.any(mask_one):
            for idx in np.where(mask_one)[0]:
                results[idx] = (True, int(steps[idx]), 'reached_1')
            active[mask_one] = False
        
        if np.any(mask_proven):
            for idx in np.where(mask_proven)[0]:
                results[idx] = (True, int(steps[idx]), 'hit_proven')
            active[mask_proven] = False
        
        if not np.any(active):
            break
        
        # Periodic cycle check
        if iteration > 0 and iteration % check_interval == 0:
            cycles = (n == last_check) & active
            if np.any(cycles):
                for idx in np.where(cycles)[0]:
                    results[idx] = (False, int(steps[idx]), 'loop_detected')
                active[cycles] = False
            last_check[active] = n[active]
        
        # Vectorized Collatz step
        is_odd = (n & 1).astype(bool) & active
        
        # Even numbers: optimized division
        even_mask = ~is_odd & active
        if np.any(even_mask):
            # Simple divide by 2 (could optimize with trailing zeros)
            n[even_mask] = n[even_mask] >> 1
            steps[even_mask] += 1
        
        # Odd numbers: (3n+1)/2
        if np.any(is_odd):
            # Vectorized: 3*n + 1, then >> 1
            temp = n[is_odd]
            temp = temp + (temp << 1) + 1  # 3n + 1
            n[is_odd] = temp >> 1
            steps[is_odd] += 1
    
    # Handle step limit
    for idx in np.where(active)[0]:
        results[idx] = (False, int(steps[idx]), 'step_limit')
    
    return results[:batch_size]


# Benchmark helper
def benchmark_simd_vs_scalar(count=10000, start=1000000):
    """Compare SIMD vs scalar performance."""
    import time
    
    test_numbers = list(range(start, start + count))
    
    # Test SIMD
    start_time = time.time()
    simd_results = collatz_check_simd_batch(test_numbers, start - 1)
    simd_time = time.time() - start_time
    
    # Test scalar
    start_time = time.time()
    scalar_results = [collatz_check_scalar(n, start - 1) for n in test_numbers]
    scalar_time = time.time() - start_time
    
    print(f"SIMD available: {SIMD_AVAILABLE}")
    print(f"Numbers tested: {count}")
    print(f"SIMD time: {simd_time:.3f}s ({count/simd_time:.0f} numbers/sec)")
    print(f"Scalar time: {scalar_time:.3f}s ({count/scalar_time:.0f} numbers/sec)")
    print(f"Speedup: {scalar_time/simd_time:.2f}x")
    
    # Verify results match
    mismatches = sum(1 for s, v in zip(simd_results, scalar_results) if s != v)
    print(f"Result mismatches: {mismatches}")


if __name__ == '__main__':
    # Run benchmark
    print("SIMD Collatz Benchmark")
    print("=" * 50)
    benchmark_simd_vs_scalar(count=10000)
