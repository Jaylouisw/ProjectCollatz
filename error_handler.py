"""
Error Handler and Logger for Collatz Engine
Catches and logs hardware issues, missing libraries, driver problems, etc.

Copyright (c) 2025 Jay (CollatzEngine)
Licensed under CC BY-NC-SA 4.0
https://creativecommons.org/licenses/by-nc-sa/4.0/
"""

import sys
import traceback
import platform
import json
from datetime import datetime
from pathlib import Path

# Error log file
ERROR_LOG_FILE = "error_log.json"

class ErrorLogger:
    """Centralized error logging for the Collatz Engine."""
    
    def __init__(self):
        self.errors = []
        self.load_existing_errors()
    
    def load_existing_errors(self):
        """Load existing error log if it exists."""
        if Path(ERROR_LOG_FILE).exists():
            try:
                with open(ERROR_LOG_FILE, 'r') as f:
                    data = json.load(f)
                    # Only keep last 100 errors
                    self.errors = data.get('errors', [])[-100:]
            except:
                self.errors = []
    
    def log_error(self, error_type, message, details=None, exception=None):
        """Log an error with full context.
        
        Args:
            error_type: Category of error (hardware, library, driver, config, etc.)
            message: Human-readable error message
            details: Additional context (dict)
            exception: The exception object if available
        """
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': message,
            'system': {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'processor': platform.processor()
            }
        }
        
        if details:
            error_entry['details'] = details
        
        if exception:
            error_entry['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception),
                'traceback': traceback.format_exc()
            }
        
        self.errors.append(error_entry)
        self.save_errors()
        
        # Also print to console
        print(f"\n[ERROR] {error_type.upper()}: {message}")
        if details:
            print(f"  Details: {details}")
    
    def save_errors(self):
        """Save error log to file."""
        try:
            with open(ERROR_LOG_FILE, 'w') as f:
                json.dump({
                    'last_updated': datetime.now().isoformat(),
                    'total_errors': len(self.errors),
                    'errors': self.errors
                }, f, indent=2)
        except Exception as e:
            print(f"Failed to save error log: {e}")
    
    def get_recent_errors(self, count=10):
        """Get the most recent errors."""
        return self.errors[-count:] if self.errors else []
    
    def clear_old_errors(self, days=30):
        """Clear errors older than specified days."""
        cutoff = datetime.now().timestamp() - (days * 86400)
        self.errors = [
            e for e in self.errors 
            if datetime.fromisoformat(e['timestamp']).timestamp() > cutoff
        ]
        self.save_errors()

# Global error logger instance
logger = ErrorLogger()

# Error checking utilities

def check_gpu_availability():
    """Check if GPU/CUDA is available and functional.
    
    Returns:
        (bool, str, dict): (success, message, details)
    """
    try:
        import cupy as cp
        
        try:
            device = cp.cuda.Device()
            props = cp.cuda.runtime.getDeviceProperties(device.id)
            mem_info = device.mem_info
            
            details = {
                'gpu_name': props['name'].decode(),
                'vram_total_gb': mem_info[1] / (1024**3),
                'vram_free_gb': mem_info[0] / (1024**3),
                'compute_capability': f"{props['major']}.{props['minor']}",
                'multiprocessor_count': props['multiProcessorCount'],
                'cuda_version': cp.cuda.runtime.runtimeGetVersion()
            }
            
            return True, "GPU available and functional", details
            
        except Exception as e:
            logger.log_error(
                'gpu_initialization',
                'GPU detected but initialization failed',
                {'stage': 'device_query'},
                e
            )
            return False, f"GPU initialization failed: {str(e)}", None
    
    except ImportError as e:
        # CuPy not installed
        return False, "CuPy library not installed (GPU mode unavailable)", None
    except Exception as e:
        logger.log_error('gpu_detection', 'Unexpected error during GPU detection', None, e)
        return False, f"GPU detection error: {str(e)}", None

def check_required_libraries():
    """Check if all required libraries are available.
    
    Returns:
        (bool, list): (all_available, missing_libraries)
    """
    required = {
        'core': ['json', 'time', 'os', 'sys', 'platform', 'datetime', 'pathlib'],
        'optional_gpu': ['cupy'],
        'multiprocessing': ['multiprocessing', 'threading', 'queue']
    }
    
    missing = []
    
    for category, libs in required.items():
        for lib in libs:
            try:
                __import__(lib)
            except ImportError:
                if category != 'optional_gpu':  # GPU libraries are optional
                    missing.append(lib)
                    logger.log_error(
                        'missing_library',
                        f'Required library missing: {lib}',
                        {'category': category}
                    )
    
    return len(missing) == 0, missing

def check_file_permissions():
    """Check if we can read/write required files.
    
    Returns:
        (bool, list): (success, issues)
    """
    issues = []
    
    # Files that must be writable
    writable_files = [
        'collatz_config.json',
        'gpu_tuning.json',
        'autotuner_state.json',
        'optimization_state.json',
        'error_log.json'
    ]
    
    for filename in writable_files:
        filepath = Path(filename)
        try:
            # Try to write test file
            if filepath.exists():
                # Check if we can read
                with open(filepath, 'r') as f:
                    f.read(1)
            else:
                # Try to create
                with open(filepath, 'a') as f:
                    pass
        except PermissionError:
            issues.append(f"No write permission for {filename}")
            logger.log_error(
                'permission_error',
                f'Cannot write to {filename}',
                {'file': str(filepath.absolute())}
            )
        except Exception as e:
            issues.append(f"File access error for {filename}: {str(e)}")
            logger.log_error(
                'file_access_error',
                f'Error accessing {filename}',
                {'file': str(filepath.absolute())},
                e
            )
    
    return len(issues) == 0, issues

def check_config_validity(config_file):
    """Check if a JSON config file is valid.
    
    Args:
        config_file: Path to config file
    
    Returns:
        (bool, str, dict): (valid, message, config_data)
    """
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return True, "Config file valid", config
    except FileNotFoundError:
        return False, f"Config file not found: {config_file}", None
    except json.JSONDecodeError as e:
        logger.log_error(
            'config_error',
            f'Invalid JSON in {config_file}',
            {'line': e.lineno, 'column': e.colno},
            e
        )
        return False, f"Invalid JSON in {config_file}: {str(e)}", None
    except Exception as e:
        logger.log_error('config_error', f'Error reading {config_file}', None, e)
        return False, f"Error reading {config_file}: {str(e)}", None

def run_system_diagnostics():
    """Run comprehensive system diagnostics.
    
    Returns:
        dict: Diagnostic results
    """
    print("=" * 70)
    print("COLLATZ ENGINE SYSTEM DIAGNOSTICS")
    print("=" * 70)
    print()
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'system': {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'processor': platform.processor()
        },
        'checks': {}
    }
    
    # Check libraries
    print("Checking required libraries...")
    libs_ok, missing = check_required_libraries()
    results['checks']['libraries'] = {
        'status': 'OK' if libs_ok else 'FAILED',
        'missing': missing
    }
    if libs_ok:
        print("  ✓ All required libraries available")
    else:
        print(f"  ✗ Missing libraries: {', '.join(missing)}")
    print()
    
    # Check GPU
    print("Checking GPU availability...")
    gpu_ok, gpu_msg, gpu_details = check_gpu_availability()
    results['checks']['gpu'] = {
        'status': 'OK' if gpu_ok else 'UNAVAILABLE',
        'message': gpu_msg,
        'details': gpu_details
    }
    if gpu_ok:
        print(f"  ✓ {gpu_msg}")
        print(f"    GPU: {gpu_details['gpu_name']}")
        print(f"    VRAM: {gpu_details['vram_total_gb']:.1f} GB")
        print(f"    Compute: {gpu_details['compute_capability']}")
    else:
        print(f"  ⚠ {gpu_msg}")
    print()
    
    # Check file permissions
    print("Checking file permissions...")
    perms_ok, perm_issues = check_file_permissions()
    results['checks']['permissions'] = {
        'status': 'OK' if perms_ok else 'FAILED',
        'issues': perm_issues
    }
    if perms_ok:
        print("  ✓ File permissions OK")
    else:
        print("  ✗ Permission issues:")
        for issue in perm_issues:
            print(f"    - {issue}")
    print()
    
    # Check config files
    print("Checking configuration files...")
    config_files = ['collatz_config.json', 'gpu_tuning.json']
    config_results = {}
    for cfg in config_files:
        if Path(cfg).exists():
            valid, msg, _ = check_config_validity(cfg)
            config_results[cfg] = {'status': 'OK' if valid else 'INVALID', 'message': msg}
            if valid:
                print(f"  ✓ {cfg}: Valid")
            else:
                print(f"  ✗ {cfg}: {msg}")
        else:
            config_results[cfg] = {'status': 'MISSING', 'message': 'File will be created on first run'}
            print(f"  ⚠ {cfg}: Will be created on first run")
    results['checks']['configs'] = config_results
    print()
    
    # Overall status
    print("=" * 70)
    all_critical_ok = libs_ok and perms_ok
    if all_critical_ok:
        print("DIAGNOSTICS: PASSED")
        if not gpu_ok:
            print("Note: GPU unavailable - CPU mode will be used")
    else:
        print("DIAGNOSTICS: FAILED")
        print("Please resolve the issues above before running")
    print("=" * 70)
    
    results['overall_status'] = 'PASSED' if all_critical_ok else 'FAILED'
    
    # Save diagnostic report
    try:
        with open('diagnostic_report.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("\nDiagnostic report saved to: diagnostic_report.json")
    except Exception as e:
        print(f"\nWarning: Could not save diagnostic report: {e}")
    
    return results

def safe_import_cupy():
    """Safely import CuPy with proper error handling.
    
    Returns:
        (module or None, bool, str): (cupy_module, success, message)
    """
    try:
        import cupy as cp
        
        # Test basic functionality
        try:
            device = cp.cuda.Device()
            _ = device.mem_info
            return cp, True, "CuPy imported and GPU accessible"
        except Exception as e:
            logger.log_error(
                'gpu_initialization',
                'CuPy imported but GPU not accessible',
                None,
                e
            )
            return None, False, f"GPU initialization failed: {str(e)}"
    
    except ImportError:
        return None, False, "CuPy not installed (use: pip install cupy-cuda12x)"
    except Exception as e:
        logger.log_error('cupy_import', 'Unexpected error importing CuPy', None, e)
        return None, False, f"CuPy import error: {str(e)}"

if __name__ == "__main__":
    # Run diagnostics when executed directly
    run_system_diagnostics()
