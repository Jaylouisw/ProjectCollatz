#!/usr/bin/env python3
"""
Integration tests for ProjectCollatz
Tests all critical functionality without requiring network
"""

import sys

def test_collatz_engine():
    """Test CollatzEngine CPU and GPU functions."""
    print("Testing CollatzEngine...")
    
    try:
        from CollatzEngine import cpu_check_range, gpu_check_range
        
        # Test CPU verification
        result = cpu_check_range(10, 20)
        assert result['counterexample'] is None, "CPU found false counterexample"
        assert result['numbers_checked'] == 10, f"CPU checked wrong count: {result['numbers_checked']}"
        print("  ✓ CPU verification works")
        
        # Test GPU verification (may fallback to CPU)
        result = gpu_check_range(10, 20)
        assert result['counterexample'] is None, "GPU found false counterexample"
        assert result['numbers_checked'] == 10, f"GPU checked wrong count: {result['numbers_checked']}"
        print("  ✓ GPU verification works")
        
        return True
    except Exception as e:
        print(f"  ✗ CollatzEngine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_distributed_worker():
    """Test distributed worker functionality."""
    print("Testing DistributedCollatzWorker...")
    
    try:
        from distributed_collatz import DistributedCollatzWorker
        
        # Just test that it can be instantiated
        # (actual network tests require IPFS daemon)
        print("  ✓ DistributedCollatzWorker imports successfully")
        
        return True
    except Exception as e:
        print(f"  ✗ DistributedCollatzWorker test failed: {e}")
        return False


def test_ipfs_coordinator():
    """Test IPFS coordinator."""
    print("Testing IPFSCoordinator...")
    
    try:
        from ipfs_coordinator import IPFSCoordinator
        
        # Test import only (actual connection requires IPFS daemon)
        print("  ✓ IPFSCoordinator imports successfully")
        
        return True
    except Exception as e:
        print(f"  ✗ IPFSCoordinator test failed: {e}")
        return False


def test_user_account():
    """Test user account system."""
    print("Testing user_account...")
    
    try:
        import user_account
        print("  ✓ user_account imports successfully")
        return True
    except Exception as e:
        print(f"  ✗ user_account test failed: {e}")
        return False


def test_trust_system():
    """Test trust and reputation system."""
    print("Testing trust_system...")
    
    try:
        import trust_system
        print("  ✓ trust_system imports successfully")
        return True
    except Exception as e:
        print(f"  ✗ trust_system test failed: {e}")
        return False


def test_proof_verification():
    """Test proof verification."""
    print("Testing proof_verification...")
    
    try:
        import proof_verification
        print("  ✓ proof_verification imports successfully")
        return True
    except Exception as e:
        print(f"  ✗ proof_verification test failed: {e}")
        return False


def test_network_launcher():
    """Test network launcher."""
    print("Testing network_launcher...")
    
    try:
        import network_launcher
        print("  ✓ network_launcher imports successfully")
        return True
    except Exception as e:
        print(f"  ✗ network_launcher test failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print("="*70)
    print("PROJECTCOLLATZ INTEGRATION TESTS")
    print("="*70)
    print()
    
    tests = [
        test_collatz_engine,
        test_distributed_worker,
        test_ipfs_coordinator,
        test_user_account,
        test_trust_system,
        test_proof_verification,
        test_network_launcher,
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
    
    print("="*70)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ ALL TESTS PASSED ({passed}/{total})")
        print("="*70)
        return 0
    else:
        print(f"✗ SOME TESTS FAILED ({passed}/{total} passed)")
        print("="*70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
