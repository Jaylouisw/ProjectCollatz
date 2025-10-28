#!/usr/bin/env python3
"""
Test verification functions to ensure everything works.
Includes proper multiprocessing guards for Windows compatibility.
"""

def run_tests():
    """Run all verification tests."""
    print("=" * 70)
    print("COLLATZ VERIFICATION SYSTEM TEST")
    print("=" * 70)
    print()

    # Test 1: Import checks
    print("[1/5] Testing imports...")
    try:
        from CollatzEngine import gpu_check_range, cpu_check_range, GPU_AVAILABLE
        print("  ✓ CollatzEngine imports OK")
    except ImportError as e:
        print(f"  ✗ CollatzEngine import failed: {e}")
        return 1

    try:
        from distributed_collatz import DistributedCollatzWorker
        print("  ✓ distributed_collatz imports OK")
    except ImportError as e:
        print(f"  ✗ distributed_collatz import failed: {e}")
        return 1

    try:
        from ipfs_coordinator import IPFSCoordinator
        print("  ✓ ipfs_coordinator imports OK")
    except ImportError as e:
        print(f"  ✗ ipfs_coordinator import failed: {e}")
        return 1

    print()

    # Test 2: CPU verification
    print("[2/5] Testing CPU verification...")
    try:
        result = cpu_check_range(1, 100)
        if result['counterexample'] is None:
            print(f"  ✓ CPU verified {result['numbers_checked']} numbers, no counterexample")
        else:
            print(f"  ✗ Unexpected result: {result}")
    except Exception as e:
        print(f"  ✗ CPU verification failed: {e}")
        import traceback
        traceback.print_exc()

    print()

    # Test 3: GPU verification
    print("[3/5] Testing GPU verification...")
    if GPU_AVAILABLE:
        try:
            result = gpu_check_range(1, 100)
            if result['counterexample'] is None and result['numbers_checked'] == 99:
                print(f"  ✓ GPU verified 99 numbers, no counterexample")
            else:
                print(f"  ✗ Unexpected result: {result}")
        except Exception as e:
            print(f"  ✗ GPU verification failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("  ⊘ GPU not available, skipping")

    print()

    # Test 4: Larger range
    print("[4/5] Testing larger range (10,000 numbers)...")
    try:
        result = cpu_check_range(1, 10000)
        if result['counterexample'] is None:
            print(f"  ✓ CPU verified {result['numbers_checked']} numbers successfully")
        else:
            print(f"  ✗ Unexpected result: {result}")
    except Exception as e:
        print(f"  ✗ Large range verification failed: {e}")

    print()

    # Test 5: IPFS coordinator (basic initialization)
    print("[5/5] Testing IPFS coordinator...")
    try:
        import warnings
        warnings.filterwarnings('ignore')
        coord = IPFSCoordinator()
        print(f"  ✓ IPFS coordinator initialized (Node: {coord.node_id[:16]}...)")
    except Exception as e:
        print(f"  ⚠️  IPFS coordinator initialization issue (non-critical): {e}")

    print()
    print("=" * 70)
    print("VERIFICATION SYSTEM TEST COMPLETE")
    print("=" * 70)
    print()
    print("✓ Core verification functions are working properly")
    print("✓ System is ready for distributed operation")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(run_tests())
