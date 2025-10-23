"""
Collatz Engine Launcher
Starts the hybrid checker, then launches the auto-tuner after 1 minute
Displays split-screen output with hybrid at top and tuner at bottom
"""

import subprocess
import time
import sys
import os
import threading
import queue
import ctypes

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
    print("=" * 70)
    print("COLLATZ ENGINE LAUNCHER")
    print("=" * 70)
    print()
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Start the hybrid checker in the background
    print("Starting Collatz Hybrid Checker...")
    hybrid_process = subprocess.Popen(
        [sys.executable, os.path.join(script_dir, "CollatzEngine.py")],
        cwd=script_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    print(f"✓ Hybrid checker started (PID: {hybrid_process.pid})")
    print()
    
    # Wait 1 minute
    print("Waiting 60 seconds before starting auto-tuner...")
    print("(This allows the hybrid checker to establish baseline performance)")
    try:
        for i in range(60, 0, -1):
            print(f"\rStarting auto-tuner in {i} seconds... ", end='', flush=True)
            time.sleep(1)
        print("\r" + " " * 50 + "\r", end='')  # Clear the countdown line
    except KeyboardInterrupt:
        print("\n\nLauncher interrupted. Stopping hybrid checker...")
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
        [sys.executable, os.path.join(script_dir, "auto_tuner.py")],
        cwd=script_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    print(f"✓ Auto-tuner started (PID: {autotuner_process.pid})")
    print()
    print("Starting split-screen view in 2 seconds...")
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
    autotuner_reader = threading.Thread(
        target=read_output,
        args=(autotuner_process.stdout, tuner_buffer, tuner_lock),
        daemon=True
    )
    
    hybrid_reader.start()
    autotuner_reader.start()
    
    # Track last display state to avoid unnecessary redraws
    last_display = ((), ())
    
    # Main display loop
    try:
        while True:
            last_display = display_split_screen(
                hybrid_buffer, tuner_buffer,
                hybrid_lock, tuner_lock,
                hybrid_process.pid, autotuner_process.pid,
                last_display
            )
            
            # Check if processes are still running
            hybrid_status = hybrid_process.poll()
            if hybrid_status is not None:
                print(f"\n[WARNING] Hybrid checker exited with code {hybrid_status}")
                autotuner_process.terminate()
                break
            
            autotuner_status = autotuner_process.poll()
            if autotuner_status is not None:
                # Tuner finished, just show hybrid
                pass
            
            time.sleep(1.0)  # Update display once per second (no flicker)
            
    except KeyboardInterrupt:
        clear_screen()
        print("\n\nStopping all processes...")
        
        # Stop auto-tuner first
        if autotuner_process.poll() is None:
            print("Stopping auto-tuner...")
            autotuner_process.terminate()
            try:
                autotuner_process.wait(timeout=3)
            except:
                autotuner_process.kill()
        
        # Stop hybrid checker
        if hybrid_process.poll() is None:
            print("Stopping hybrid checker...")
            hybrid_process.terminate()
            try:
                hybrid_process.wait(timeout=5)
            except:
                hybrid_process.kill()
        
        print("All processes stopped.")

if __name__ == "__main__":
    main()
