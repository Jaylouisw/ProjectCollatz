"""
Collatz Engine Launcher
Starts the CollatzEngine, then automatically launches auto-tuner if needed
Displays split-screen output with engine at top and tuner at bottom
Automatically detects if optimization is needed based on hardware

Copyright (c) 2025 Jay (CollatzEngine)
Licensed under CC BY-NC-SA 4.0
https://creativecommons.org/licenses/by-nc-sa/4.0/
"""

import subprocess
import time
import sys
import os
import threading
import queue
import ctypes
import optimization_state

# Import error handler
try:
    from error_handler import logger, run_system_diagnostics
    ERROR_HANDLING = True
except ImportError:
    ERROR_HANDLING = False
    logger = None

# Windows console API for flicker-free updates
if os.name == 'nt':
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

def read_output(pipe, buffer, lock):
    """Read lines from a subprocess pipe and store in buffer."""
    try:
        for line in iter(pipe.readline, ''):
            if line:
                with lock:
                    buffer.append(line.rstrip('\n\r'))
                    # Keep last 100 lines
                    if len(buffer) > 100:
                        buffer.pop(0)
    except:
        pass
    finally:
        pipe.close()

def clear_screen():
    """Clear the terminal screen."""
    # Use ANSI escape codes for smoother refresh (no flicker)
    print("\033[2J\033[H", end='', flush=True)

def display_split_screen(hybrid_buffer, tuner_buffer, hybrid_lock, tuner_lock, hybrid_pid, tuner_pid, last_display):
    """Display split screen with hybrid output at top and tuner at bottom.
    Only redraw if content has actually changed."""
    
    # Build new display content
    with hybrid_lock:
        hybrid_lines = hybrid_buffer[-15:]  # Show last 15 lines
    
    with tuner_lock:
        tuner_lines = tuner_buffer[-15:]  # Show last 15 lines
    
    # Create current display state
    current_display = (tuple(hybrid_lines), tuple(tuner_lines))
    
    # Only redraw if content changed
    if current_display == last_display:
        return last_display
    
    separator_line = "=" * 70
    
    # Move cursor to home position
    print("\033[H", end='', flush=True)
    
    # Header
    print("COLLATZ ENGINE - SPLIT VIEW\033[K")
    print(f"{separator_line}\033[K")
    
    # Hybrid section (top half)
    print(f"HYBRID CHECKER (PID: {hybrid_pid})\033[K")
    print(f"{'-' * 70}\033[K")
    
    for line in hybrid_lines:
        print(f"{line[:70]}\033[K")
    
    # Fill empty lines
    for _ in range(15 - len(hybrid_lines)):
        print("\033[K")
    
    # Middle separator
    print(f"{separator_line}\033[K")
    
    # Tuner section (bottom half)
    print(f"AUTO-TUNER (PID: {tuner_pid})\033[K")
    print(f"{'-' * 70}\033[K")
    
    for line in tuner_lines:
        print(f"{line[:70]}\033[K")
    
    # Fill empty lines
    for _ in range(15 - len(tuner_lines)):
        print("\033[K")
    
    print(f"{separator_line}\033[K")
    print("Press Ctrl+C to stop both processes\033[K")
    
    # Clear any remaining lines
    for _ in range(3):
        print("\033[K")
    
    sys.stdout.flush()
    
    return current_display
    print("Press Ctrl+C to stop both processes")

def main():
    # Check for --diagnostics flag
    if '--diagnostics' in sys.argv:
        if ERROR_HANDLING:
            run_system_diagnostics()
            return
        else:
            print("Error: Diagnostics not available - error_handler.py not found")
            return
    
    print("=" * 70)
    print("COLLATZ ENGINE LAUNCHER")
    print("=" * 70)
    print()
    
    # Quick system check if error handling available
    if ERROR_HANDLING:
        try:
            from error_handler import check_required_libraries, check_gpu_availability
            libs_ok, missing = check_required_libraries()
            if not libs_ok:
                logger.log_error('startup', 'Missing required libraries', {'missing': missing})
                print(f"[ERROR] Missing required libraries: {', '.join(missing)}")
                print("[ERROR] Please install missing dependencies")
                print("\nRun with --diagnostics flag for detailed system check:")
                print("  python launcher.py --diagnostics")
                return
        except Exception as e:
            print(f"[WARNING] Pre-flight check failed: {e}")
    
    # Check optimization status
    opt_status = optimization_state.get_optimization_status()
    
    print("System Status Check:")
    print(f"  Status: {opt_status['status']}")
    print(f"  Reason: {opt_status['reason']}")
    print()
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Determine if we should run auto-tuner
    should_run_tuner = opt_status['needs_optimization']
    
    if should_run_tuner:
        print("[AUTO-TUNER] Will automatically start - optimization needed")
    else:
        print("[AUTO-TUNER] Skipping - system already optimized")
        if opt_status['benchmark_ready']:
            print("[BENCHMARK] Final benchmark recommended - run: python benchmark.py")
    print()
    
    # Ask user for mode selection
    print("Select execution mode:")
    print("  1) GPU mode (GPU + CPU workers)")
    print("  2) CPU-only mode")
    print("  3) Auto-detect (default)")
    print()
    
    mode_choice = input("Enter choice (1/2/3 or press Enter for auto): ").strip()
    
    if mode_choice == '1':
        mode_arg = 'gpu'
    elif mode_choice == '2':
        mode_arg = 'cpu'
    else:
        mode_arg = None  # Auto-detect
    
    print()
    
    # Start the CollatzEngine in the background
    print("Starting Collatz Engine...")
    engine_cmd = [sys.executable, os.path.join(script_dir, "CollatzEngine.py")]
    if mode_arg:
        engine_cmd.append(mode_arg)
    
    hybrid_process = subprocess.Popen(
        engine_cmd,
        cwd=script_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    print(f"[ENGINE] Started (PID: {hybrid_process.pid})")
    print()
    
    autotuner_process = None
    
    if should_run_tuner:
        # Wait 60 seconds before starting auto-tuner
        print("Waiting 60 seconds before starting auto-tuner...")
        print("(This allows the engine to establish baseline performance)")
        try:
            for i in range(60, 0, -1):
                print(f"\rStarting auto-tuner in {i} seconds... ", end='', flush=True)
                time.sleep(1)
            print("\r" + " " * 50 + "\r", end='')  # Clear the countdown line
        except KeyboardInterrupt:
            print("\n\nLauncher interrupted. Stopping engine...")
            hybrid_process.terminate()
            try:
                hybrid_process.wait(timeout=5)
            except:
                hybrid_process.kill()
            print("Stopped.")
            return
        
        # Start the auto-tuner
        print("Starting Auto-Tuner...")
        autotuner_process = subprocess.Popen(
            [sys.executable, os.path.join(script_dir, "auto_tuner.py"), "--auto-resume"],
            cwd=script_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        print(f"[TUNER] Started (PID: {autotuner_process.pid})")
        print()
        print("Starting split-screen view in 2 seconds...")
        time.sleep(2)
    else:
        print("Running in single-screen mode (no auto-tuner needed)")
        print()
        time.sleep(2)
    
    # Create output buffers and locks
    hybrid_buffer = []
    tuner_buffer = []
    hybrid_lock = threading.Lock()
    tuner_lock = threading.Lock()
    
    # Start reader threads
    hybrid_reader = threading.Thread(
        target=read_output, 
        args=(hybrid_process.stdout, hybrid_buffer, hybrid_lock),
        daemon=True
    )
    hybrid_reader.start()
    
    if autotuner_process:
        autotuner_reader = threading.Thread(
            target=read_output,
            args=(autotuner_process.stdout, tuner_buffer, tuner_lock),
            daemon=True
        )
        autotuner_reader.start()
    
    # Track last display state to avoid unnecessary redraws
    last_display = ((), ())
    
    # Main display loop
    try:
        while True:
            tuner_pid = autotuner_process.pid if autotuner_process else None
            last_display = display_split_screen(
                hybrid_buffer, tuner_buffer if autotuner_process else [],
                hybrid_lock, tuner_lock,
                hybrid_process.pid, tuner_pid,
                last_display
            )
            
            # Check if processes are still running
            hybrid_status = hybrid_process.poll()
            if hybrid_status is not None:
                print(f"\n[WARNING] Engine exited with code {hybrid_status}")
                if autotuner_process:
                    autotuner_process.terminate()
                break
            
            if autotuner_process:
                autotuner_status = autotuner_process.poll()
                if autotuner_status is not None:
                    # Tuner finished - mark optimization complete
                    print(f"\n[TUNER] Auto-tuner completed with code {autotuner_status}")
                    if autotuner_status == 0:
                        optimization_state.mark_optimization_complete()
                        print("[OPTIMIZATION] System is now optimized!")
                        print("[BENCHMARK] Run 'python benchmark.py' for final benchmark")
                    autotuner_process = None  # Don't check again
            
            time.sleep(1.0)  # Update display once per second (no flicker)
            
    except KeyboardInterrupt:
        clear_screen()
        print("\n\nStopping all processes...")
        
        # Stop auto-tuner first (if running)
        if autotuner_process and autotuner_process.poll() is None:
            print("Stopping auto-tuner...")
            autotuner_process.terminate()
            try:
                autotuner_process.wait(timeout=3)
            except:
                autotuner_process.kill()
        
        # Stop engine
        if hybrid_process.poll() is None:
            print("Stopping engine...")
            hybrid_process.terminate()
            try:
                hybrid_process.wait(timeout=5)
            except:
                hybrid_process.kill()
        
        print("All processes stopped.")

if __name__ == "__main__":
    main()
