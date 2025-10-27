#!/usr/bin/env python3
'''
COLLATZ DISTRIBUTED NETWORK - MAIN LAUNCHER
============================================

Single entry point for all network operations.
Just run: python network_launcher.py

Only one instance can run per machine.
'''

import subprocess
import sys
import os
import tempfile
from typing import Optional

# Platform-specific imports
if os.name != 'nt':
    import fcntl



class SingleInstanceLock:
    """Ensures only one instance of the launcher runs per machine."""
    
    def __init__(self, lock_name='collatz_launcher'):
        self.lock_file = None
        self.lock_name = lock_name
        
        # Use platform-appropriate lock location
        if os.name == 'nt':
            # Windows: use temp directory
            lock_dir = tempfile.gettempdir()
        else:
            # Unix-like: try /var/lock first, fallback to temp
            lock_dir = '/var/lock' if os.path.exists('/var/lock') else tempfile.gettempdir()
        
        self.lock_path = os.path.join(lock_dir, f'{lock_name}.lock')
    
    def acquire(self):
        """Acquire the lock. Returns True if successful, False if another instance is running."""
        try:
            self.lock_file = open(self.lock_path, 'w')
            
            if os.name == 'nt':
                # Windows: try to lock using msvcrt
                import msvcrt
                try:
                    msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    self.lock_file.write(str(os.getpid()))
                    self.lock_file.flush()
                    return True
                except IOError:
                    return False
            else:
                # Unix-like: use fcntl
                try:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.lock_file.write(str(os.getpid()))
                    self.lock_file.flush()
                    return True
                except IOError:
                    return False
        except Exception as e:
            print(f"Error acquiring lock: {e}")
            return False
    
    def release(self):
        """Release the lock."""
        if self.lock_file:
            try:
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.lock_file.close()
                if os.path.exists(self.lock_path):
                    os.remove(self.lock_path)
            except:
                pass
    
    def __enter__(self):
        if not self.acquire():
            raise RuntimeError("Another instance is already running")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class CollatzLauncher:
    def __init__(self):
        self.clear_screen()
        self.running = True
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        print("=" * 70)
        print("    COLLATZ DISTRIBUTED VERIFICATION NETWORK")
        print("=" * 70)
        print()
    
    def print_menu(self):
        self.clear_screen()
        self.print_header()
        print("MAIN MENU:")
        print()
        print("  WORKER NODE:")
        print("    1. Start Worker Node (with account)")
        print("    2. Start Worker Node (anonymous)")
        print("    3. Start Worker Node (CPU-only)")
        print()
        print("  USER ACCOUNTS:")
        print("    4. Create User Account")
        print("    5. View User Statistics")
        print("    6. View Leaderboard")
        print()
        print("  NETWORK MANAGEMENT:")
        print("    7. Generate Work Assignments")
        print("    8. Update IPFS Leaderboard Webpage")
        print("    9. View Network Statistics")
        print()
        print("  SYSTEM:")
        print("   10. Run Diagnostics")
        print("   11. Check IPFS Status")
        print()
        print("    0. Exit")
        print()
    
    def get_choice(self):
        try:
            choice = input("Enter choice: ").strip()
            return int(choice)
        except ValueError:
            return None
    
    def list_available_accounts(self):
        keys_dir = "./keys"
        if not os.path.exists(keys_dir):
            print("No keys directory found. Create an account first (option 4).")
            return []
        
        key_files = [f for f in os.listdir(keys_dir) if f.endswith("_private_key.pem")]
        
        if not key_files:
            print("No user accounts found. Create one first (option 4).")
            return []
        
        print("\nAvailable accounts:")
        for i, key_file in enumerate(key_files, 1):
            username = key_file.replace("_private_key.pem", "")
            print(f"  {i}. {username}")
        print()
        
        return key_files
    
    def start_worker_with_account(self):
        self.clear_screen()
        self.print_header()
        print("START WORKER NODE (WITH ACCOUNT)")
        print("-" * 70)
        print()
        
        key_files = self.list_available_accounts()
        if not key_files:
            input("\nPress ENTER to continue...")
            return
        
        try:
            choice = int(input("Select account number (0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(key_files):
                key_path = os.path.join("./keys", key_files[choice - 1])
                print(f"\nStarting worker with account: {key_path}")
                print("Press Ctrl+C to stop the worker.")
                print()
                subprocess.run([sys.executable, "distributed_collatz.py", "--user-key", key_path])
            else:
                print("Invalid choice.")
                input("\nPress ENTER to continue...")
        except ValueError:
            print("Invalid input.")
            input("\nPress ENTER to continue...")
        except KeyboardInterrupt:
            print("\n\nWorker stopped by user.")
            input("\nPress ENTER to continue...")
    
    def start_worker_anonymous(self):
        self.clear_screen()
        self.print_header()
        print("START WORKER NODE (ANONYMOUS)")
        print("-" * 70)
        print()
        print("Starting anonymous worker node...")
        print("Press Ctrl+C to stop the worker.")
        print()
        
        try:
            subprocess.run([sys.executable, "distributed_collatz.py"])
        except KeyboardInterrupt:
            print("\n\nWorker stopped by user.")
            input("\nPress ENTER to continue...")
    
    def start_worker_cpu_only(self):
        self.clear_screen()
        self.print_header()
        print("START WORKER NODE (CPU-ONLY)")
        print("-" * 70)
        print()
        
        use_account = input("Use account? (y/n): ").strip().lower()
        
        cmd = [sys.executable, "distributed_collatz.py", "--cpu-only"]
        
        if use_account == 'y':
            key_files = self.list_available_accounts()
            if key_files:
                try:
                    choice = int(input("Select account number (0 to cancel): "))
                    if choice == 0:
                        return
                    if 1 <= choice <= len(key_files):
                        key_path = os.path.join("./keys", key_files[choice - 1])
                        cmd.extend(["--user-key", key_path])
                except ValueError:
                    print("Invalid input.")
                    input("\nPress ENTER to continue...")
                    return
        
        print("\nStarting CPU-only worker...")
        print("Press Ctrl+C to stop the worker.")
        print()
        
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print("\n\nWorker stopped by user.")
            input("\nPress ENTER to continue...")
    
    def create_user_account(self):
        self.clear_screen()
        self.print_header()
        print("CREATE USER ACCOUNT")
        print("-" * 70)
        print()
        
        username = input("Enter username: ").strip()
        if not username:
            print("Username cannot be empty.")
            input("\nPress ENTER to continue...")
            return
        
        print()
        subprocess.run([sys.executable, "user_account.py", "create", username])
        input("\nPress ENTER to continue...")
    
    def view_user_stats(self):
        self.clear_screen()
        self.print_header()
        print("VIEW USER STATISTICS")
        print("-" * 70)
        print()
        
        user_id = input("Enter user ID (or leave empty to view all): ").strip()
        print()
        
        if user_id:
            subprocess.run([sys.executable, "user_account.py", "stats", user_id])
        else:
            subprocess.run([sys.executable, "user_account.py", "stats"])
        
        input("\nPress ENTER to continue...")
    
    def view_leaderboard(self):
        self.clear_screen()
        self.print_header()
        print("VIEW LEADERBOARD")
        print("-" * 70)
        print()
        
        limit = input("Number of top users to show (default 10): ").strip()
        print()
        
        cmd = [sys.executable, "user_account.py", "leaderboard"]
        if limit:
            try:
                cmd.extend(["--limit", str(int(limit))])
            except ValueError:
                print("Invalid number, using default (10).")
        
        subprocess.run(cmd)
        input("\nPress ENTER to continue...")
    
    def generate_work(self):
        self.clear_screen()
        self.print_header()
        print("GENERATE WORK ASSIGNMENTS")
        print("-" * 70)
        print()
        
        count = input("Number of assignments to generate (default 100): ").strip()
        print()
        
        if not count:
            count = "100"
        
        try:
            count_int = int(count)
            print(f"Generating {count_int} work assignments...")
            subprocess.run([sys.executable, "distributed_collatz.py", "--generate-work", count])
        except ValueError:
            print("Invalid number.")
        
        input("\nPress ENTER to continue...")
    
    def update_leaderboard_webpage(self):
        self.clear_screen()
        self.print_header()
        print("UPDATE IPFS LEADERBOARD WEBPAGE")
        print("-" * 70)
        print()
        
        print("Generating HTML leaderboard and publishing to IPFS...")
        print()
        subprocess.run([sys.executable, "leaderboard_generator.py"])
        input("\nPress ENTER to continue...")
    
    def view_network_stats(self):
        self.clear_screen()
        self.print_header()
        print("VIEW NETWORK STATISTICS")
        print("-" * 70)
        print()
        
        try:
            from ipfs_coordinator import IPFSCoordinator
            coordinator = IPFSCoordinator()
            
            active_workers = coordinator.active_workers
            print(f"Active Workers: {len(active_workers)}")
            print()
            
            if os.path.exists("assignments.json"):
                import json
                with open("assignments.json", 'r') as f:
                    assignments = json.load(f)
                
                total = len(assignments.get("available", [])) + len(assignments.get("in_progress", [])) + len(assignments.get("completed", []))
                available = len(assignments.get("available", []))
                in_progress = len(assignments.get("in_progress", []))
                completed = len(assignments.get("completed", []))
                
                print(f"Total Assignments: {total}")
                print(f"  Available:   {available}")
                print(f"  In Progress: {in_progress}")
                print(f"  Completed:   {completed}")
                print()
            
            if os.path.exists("collatz_config.json"):
                import json
                with open("collatz_config.json", 'r') as f:
                    config = json.load(f)
                
                print(f"Network Frontier: {config.get('current', 'Unknown')}")
                print()
        
        except Exception as e:
            print(f"Error retrieving network stats: {e}")
        
        input("\nPress ENTER to continue...")
    
    def run_diagnostics(self):
        self.clear_screen()
        self.print_header()
        print("RUN DIAGNOSTICS")
        print("-" * 70)
        print()
        
        print("Running system diagnostics...")
        print()
        subprocess.run([sys.executable, "run_diagnostics.py"])
        input("\nPress ENTER to continue...")
    
    def check_ipfs_status(self):
        self.clear_screen()
        self.print_header()
        print("CHECK IPFS STATUS")
        print("-" * 70)
        print()
        
        try:
            from ipfs_coordinator import IPFSCoordinator
            coordinator = IPFSCoordinator()
            
            print("OK IPFS daemon is running")
            print(f"  Node ID: {coordinator.client.id()['ID']}")
            print()
        except Exception as e:
            print("X IPFS daemon not running or not accessible")
            print(f"  Error: {e}")
            print()
            print("Start IPFS with: ipfs daemon")
            print()
        
        input("\nPress ENTER to continue...")
    
    def run(self):
        while self.running:
            self.print_menu()
            choice = self.get_choice()
            
            if choice == 0:
                self.running = False
                print("\nExiting launcher. Goodbye!")
            elif choice == 1:
                self.start_worker_with_account()
            elif choice == 2:
                self.start_worker_anonymous()
            elif choice == 3:
                self.start_worker_cpu_only()
            elif choice == 4:
                self.create_user_account()
            elif choice == 5:
                self.view_user_stats()
            elif choice == 6:
                self.view_leaderboard()
            elif choice == 7:
                self.generate_work()
            elif choice == 8:
                self.update_leaderboard_webpage()
            elif choice == 9:
                self.view_network_stats()
            elif choice == 10:
                self.run_diagnostics()
            elif choice == 11:
                self.check_ipfs_status()
            else:
                print("\nInvalid choice. Please try again.")
                input("\nPress ENTER to continue...")


def main():
    """Main entry point with single-instance lock."""
    try:
        # Acquire single-instance lock
        with SingleInstanceLock('collatz_launcher'):
            launcher = CollatzLauncher()
            launcher.run()
    except RuntimeError as e:
        print("=" * 70)
        print("    COLLATZ DISTRIBUTED VERIFICATION NETWORK")
        print("=" * 70)
        print()
        print("ERROR: Another instance of the launcher is already running!")
        print()
        print("Only one launcher instance can run per machine.")
        print("If you're sure no other instance is running, the lock file may be stale.")
        print()
        if os.name == 'nt':
            lock_path = os.path.join(tempfile.gettempdir(), 'collatz_launcher.lock')
        else:
            lock_dir = '/var/lock' if os.path.exists('/var/lock') else tempfile.gettempdir()
            lock_path = os.path.join(lock_dir, 'collatz_launcher.lock')
        print(f"Lock file location: {lock_path}")
        print("You can manually delete this file if needed.")
        print()
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nLauncher interrupted by user. Goodbye!")
        sys.exit(0)


if __name__ == '__main__':
    main()
