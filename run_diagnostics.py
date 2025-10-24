"""
Collatz Engine System Diagnostics
Run this script to check for hardware issues, missing libraries, driver problems, etc.

Copyright (c) 2025 Jay (CollatzEngine)
Licensed under CC BY-NC-SA 4.0
https://creativecommons.org/licenses/by-nc-sa/4.0/
"""

if __name__ == "__main__":
    try:
        from error_handler import run_system_diagnostics
        print("\nRunning Collatz Engine System Diagnostics...\n")
        results = run_system_diagnostics()
        
        print("\n" + "=" * 70)
        print("NEXT STEPS")
        print("=" * 70)
        
        if results['overall_status'] == 'PASSED':
            print("✓ Your system is ready to run Collatz Engine")
            print("\nTo start:")
            print("  python launcher.py        - Run with automatic optimization")
            print("  python CollatzEngine.py   - Run engine directly")
            print("  python benchmark.py       - Run performance benchmark")
        else:
            print("✗ Issues detected - please resolve before running")
            print("\nCommon fixes:")
            if not results['checks']['libraries']['status'] == 'OK':
                print("  - Install missing Python libraries")
            if results['checks']['gpu']['status'] != 'OK':
                print("  - For GPU mode: Install CuPy (pip install cupy-cuda12x)")
                print("  - For CPU mode: This is optional, CPU mode will work fine")
            if not results['checks']['permissions']['status'] == 'OK':
                print("  - Fix file permissions (run as administrator or check folder access)")
        
        print("\nFor detailed error history:")
        print("  Check error_log.json")
        print("=" * 70)
        
    except ImportError:
        print("ERROR: error_handler.py not found")
        print("Please ensure all Collatz Engine files are present")
    except Exception as e:
        print(f"ERROR: Diagnostics failed: {e}")
        import traceback
        traceback.print_exc()
