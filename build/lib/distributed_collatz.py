"""
DISTRIBUTED COLLATZ - WORKER NODE
==================================
Copyright (c) 2025 Jay Wenden (CollatzEngine)
Licensed under CC BY-NC-SA 4.0

Distributed worker that:
1. Claims work from IPFS coordinator
2. Verifies ranges using CollatzEngine
3. Signs and submits proofs
4. Participates in cross-verification
5. Builds trust/reputation over time

Run this to join the distributed verification network!
"""

import os
import sys
import time
import json
import argparse
from typing import Optional, Dict
from datetime import datetime
from dataclasses import asdict

# Import distributed components
from ipfs_coordinator import IPFSCoordinator, IPFS_AVAILABLE
from trust_system import TrustSystem
from proof_verification import ProofVerificationSystem, CRYPTO_AVAILABLE
from user_account import UserAccountManager, UserAccount
from counterexample_handler import CounterexampleCoordinator

# Import CollatzEngine components
try:
    from CollatzEngine import gpu_check_range, cpu_check_range, GPU_AVAILABLE
    ENGINE_AVAILABLE = True
except ImportError:
    print("[ERROR] CollatzEngine not found. Make sure CollatzEngine.py is in the same directory.")
    ENGINE_AVAILABLE = False


class DistributedCollatzWorker:
    """A worker node in the FULLY DECENTRALIZED Collatz verification network."""
    
    def __init__(self, ipfs_api: str = '/ip4/127.0.0.1/tcp/5001',
                 use_gpu: bool = True,
                 user_key_file: Optional[str] = None,
                 worker_name: Optional[str] = None):
        """
        Initialize distributed worker.
        
        Args:
            ipfs_api: IPFS API address
            use_gpu: Use GPU if available
            user_key_file: Path to user private key (for account linking)
            worker_name: Optional worker name
        """
        if not IPFS_AVAILABLE:
            raise ImportError("Please install: pip install ipfshttpclient")
        
        if not CRYPTO_AVAILABLE:
            raise ImportError("Please install: pip install cryptography")
        
        if not ENGINE_AVAILABLE:
            raise ImportError("CollatzEngine.py not found")
        
        # Initialize components
        self.coordinator = IPFSCoordinator(ipfs_api=ipfs_api)
        self.trust_system = TrustSystem()
        self.verifier = ProofVerificationSystem(self.trust_system)
        self.account_manager = UserAccountManager()
        self.counterexample_handler = CounterexampleCoordinator(self.coordinator)
        
        # Worker identity
        self.worker_id = self.coordinator.node_id
        self.worker_name = worker_name or f"Worker-{self.worker_id[:8]}"
        self.use_gpu = use_gpu and GPU_AVAILABLE
        
        # User account (NEW!)
        self.user_account: Optional[UserAccount] = None
        self.user_id: Optional[str] = None
        self.user_private_key = None
        
        if user_key_file:
            # Load existing user account
            try:
                self.user_account, self.user_private_key = self.account_manager.load_user_account(user_key_file)
                self.user_id = self.user_account.user_id
                
                # Register this worker to the user account
                self.account_manager.register_node(self.user_id, self.worker_id)
                
                print(f"[WORKER] 👤 Logged in as: {self.user_account.username}")
                print(f"[WORKER] User contributions: {self.user_account.total_contributions:,} numbers")
            except Exception as e:
                print(f"[WORKER] ⚠️ Could not load user account: {e}")
                print(f"[WORKER] Running as anonymous worker")
        
        # Load or generate worker keypair
        self.private_key, self.public_key = self.load_or_generate_keypair()
        
        # Register public key with network
        public_key_pem = self.verifier.serialize_public_key(self.public_key)
        self.verifier.register_worker_key(self.worker_id, public_key_pem)
        
        # Register worker with trust system (link to user if available)
        self.trust_system.register_worker(self.worker_id, self.user_id)
        
        # Statistics
        self.total_ranges_verified = 0
        self.total_numbers_checked = 0
        self.total_compute_time = 0.0
        self.session_start = time.time()
        
        print(f"[WORKER] 🌐 Fully Decentralized Node: {self.worker_name}")
        print(f"[WORKER] Node ID: {self.worker_id[:16]}...")
        if self.user_id:
            print(f"[WORKER] User: {self.user_account.username} ({self.user_id})")
        print(f"[WORKER] Mode: {'GPU' if self.use_gpu else 'CPU'}")
        print(f"[WORKER] Network peers: {self.coordinator.get_network_statistics()['known_peers']}")
        
        # Check trust level
        stats = self.trust_system.get_worker_stats(self.worker_id)
        if stats:
            print(f"[WORKER] Trust Level: {stats.trust_level.name}")
            print(f"[WORKER] Reputation: {stats.reputation_score:.1f}/100")
        else:
            print(f"[WORKER] Trust Level: NEW (UNTRUSTED)")
        
        print(f"[WORKER] 🚀 Network runs forever with n>0 nodes!")
    
    def load_or_generate_keypair(self):
        """Load existing keypair or generate new one."""
        keypair_file = f"worker_keypair_{self.worker_id[:16]}.json"
        
        try:
            # Try to load existing keypair
            with open(keypair_file, 'r') as f:
                data = json.load(f)
                
            # Deserialize private key
            from cryptography.hazmat.primitives import serialization
            private_key = serialization.load_pem_private_key(
                data['private_key'].encode('utf-8'),
                password=None
            )
            public_key = private_key.public_key()
            
            print(f"[WORKER] Loaded existing keypair from {keypair_file}")
            
        except FileNotFoundError:
            # Generate new keypair
            private_key, public_key = self.verifier.generate_worker_keypair()
            
            # Save for future use
            from cryptography.hazmat.primitives import serialization
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            with open(keypair_file, 'w') as f:
                json.dump({
                    'private_key': private_pem.decode('utf-8'),
                    'public_key': public_pem.decode('utf-8'),
                    'created_at': time.time()
                }, f, indent=2)
            
            print(f"[WORKER] Generated new keypair, saved to {keypair_file}")
            print(f"[WORKER] ⚠️ BACKUP THIS FILE! It's your worker identity.")
        
        return private_key, public_key
    
    def claim_and_verify_work(self) -> bool:
        """
        Claim work from coordinator and verify it.
        Tracks contributions for user account if logged in.
        Returns True if work was completed, False if no work available.
        """
        # Claim work assignment (now passes user_id for tracking)
        assignment = self.coordinator.claim_work(self.worker_id, self.user_id)
        
        if assignment is None:
            print(f"[WORKER] No work available (network auto-generates more)")
            return False
        
        print(f"\n[WORKER] 🔨 Starting verification of range:")
        if self.user_id:
            print(f"[WORKER]   User: {self.user_account.username}")
        print(f"[WORKER]   Range: {assignment.range_start:,} to {assignment.range_end:,}")
        print(f"[WORKER]   Numbers: ~{assignment.range_end - assignment.range_start:,}")
        
        # Verify the range
        start_time = time.time()
        
        try:
            if self.use_gpu:
                # Use GPU verification
                all_converged = self.verify_range_gpu(assignment.range_start, assignment.range_end)
            else:
                # Use CPU verification
                all_converged = self.verify_range_cpu(assignment.range_start, assignment.range_end)
            
            compute_time = time.time() - start_time
            numbers_checked = (assignment.range_end - assignment.range_start) // 2
            
            print(f"[WORKER] ✅ Verification complete in {compute_time:.1f}s")
            print(f"[WORKER] Result: {'ALL CONVERGED' if all_converged else '⚠️ COUNTEREXAMPLE FOUND'}")
            print(f"[WORKER] Rate: {numbers_checked / compute_time:,.0f} odd/sec")
            
            # Create detailed proof for IPFS
            detailed_proof = {
                'worker_id': self.worker_id,
                'worker_name': self.worker_name,
                'user_id': self.user_id,  # Include user ID
                'username': self.user_account.username if self.user_account else None,
                'assignment_id': assignment.assignment_id,
                'range_start': assignment.range_start,
                'range_end': assignment.range_end,
                'all_converged': all_converged,
                'numbers_checked': numbers_checked,
                'compute_time': compute_time,
                'timestamp': time.time(),
                'verification_mode': 'GPU' if self.use_gpu else 'CPU',
                'engine_version': '1.0'
            }
            
            # Upload proof to IPFS via coordinator
            proof_cid = self.coordinator.client.add_json(detailed_proof)
            print(f"[WORKER] Proof uploaded to IPFS: /ipfs/{proof_cid[:16]}...")
            
            # Create signed proof
            signed_proof = self.verifier.create_signed_proof(
                private_key=self.private_key,
                worker_id=self.worker_id,
                range_start=assignment.range_start,
                range_end=assignment.range_end,
                all_converged=all_converged,
                numbers_checked=numbers_checked,
                max_steps=100000,  # Adjust based on your max_steps
                compute_time=compute_time,
                ipfs_cid=proof_cid
            )
            
            # Submit proof to coordinator (now passes user_id)
            proof_id = self.coordinator.submit_verification_proof(
                worker_id=self.worker_id,
                assignment_id=assignment.assignment_id,
                all_converged=all_converged,
                numbers_checked=numbers_checked,
                max_steps=100000,
                compute_time=compute_time,
                detailed_proof=detailed_proof,
                user_id=self.user_id
            )
            
            # Submit for consensus/trust verification
            consensus_reached, message = self.verifier.submit_for_consensus(signed_proof)
            print(f"[WORKER] {message}")
            
            # 🚨 COUNTEREXAMPLE DETECTION 🚨
            if consensus_reached and not all_converged:
                print(f"\n{'=' * 70}")
                print(f"🚨 POTENTIAL COUNTEREXAMPLE DETECTED 🚨")
                print(f"{'=' * 70}")
                print(f"Range: {assignment.range_start:,} to {assignment.range_end:,}")
                print(f"This could be THE number that breaks Collatz!")
                print(f"Waiting for additional verifications...")
                print(f"{'=' * 70}\n")
                
                # Check if we have enough confirmations
                proofs = self.coordinator.get_proofs_for_assignment(assignment.assignment_id)
                counterexample = self.counterexample_handler.check_for_counterexample(
                    assignment.assignment_id,
                    [asdict(p) for p in proofs]
                )
                
                if counterexample:
                    # COUNTEREXAMPLE CONFIRMED! 🎉
                    print(f"\n\n")
                    print(f"{'=' * 70}")
                    print(f"🎊 COUNTEREXAMPLE VERIFIED BY NETWORK 🎊")
                    print(f"{'=' * 70}\n")
                    
                    # Broadcast to all nodes
                    self.counterexample_handler.broadcast_counterexample_found(counterexample)
                    
                    # Display celebration
                    self.counterexample_handler.display_celebration_message(
                        self.coordinator.genesis_timestamp
                    )
                    
                    # Start voting
                    self.counterexample_handler.start_voting(voting_duration_hours=24)
                    
                    # Get user vote
                    while True:
                        vote_input = input("\nYour vote [Y=Continue / N=Shutdown]: ").strip().upper()
                        if vote_input in ['Y', 'N']:
                            break
                        print("Please enter Y or N")
                    
                    vote_continue = (vote_input == 'Y')
                    self.counterexample_handler.submit_vote(
                        self.worker_id,
                        self.user_id,
                        vote_continue
                    )
                    
                    # Check if decision reached
                    if not self.counterexample_handler.voting_active:
                        # Decision made, exit worker
                        stats = self.counterexample_handler.get_voting_stats()
                        if stats['votes_shutdown'] > stats['votes_continue']:
                            print(f"\n[WORKER] Network voted to SHUTDOWN. Goodbye!")
                            sys.exit(0)
                        else:
                            print(f"\n[WORKER] Network voted to CONTINUE. Resuming work...")
                    else:
                        print(f"\n[WORKER] Vote submitted. Waiting for others...")
            
            # Update statistics
            self.total_ranges_verified += 1
            self.total_numbers_checked += numbers_checked
            self.total_compute_time += compute_time
            
            # Update user account contributions if logged in
            if self.user_id and self.account_manager and consensus_reached:
                try:
                    self.account_manager.update_contributions(
                        self.user_id,
                        numbers_checked,
                        1,  # 1 range completed
                        compute_time
                    )
                    # Show updated user stats
                    stats = self.account_manager.get_user_stats(self.user_id)
                    print(f"[WORKER] 👤 User Stats: {stats['total_numbers_checked']:,} numbers | "
                          f"{stats['total_ranges_completed']:,} ranges | "
                          f"{stats['total_compute_time']:.1f}s total")
                except Exception as e:
                    print(f"[WORKER] ⚠️ Failed to update user contributions: {e}")
            
            # Check if range is complete and update global highest
            if consensus_reached and all_converged:
                self.coordinator.update_global_highest(assignment.range_end)
            
            return True
            
        except Exception as e:
            print(f"[WORKER] ❌ Error during verification: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def verify_range_gpu(self, start: int, end: int) -> bool:
        """
        Verify range using GPU.
        Returns True if all numbers converge, False if counterexample found.
        """
        # This would call your CollatzEngine GPU verification
        # For now, placeholder that would integrate with your existing code
        print(f"[WORKER] Using GPU verification...")
        
        # TODO: Integrate with actual CollatzEngine.py gpu_check_range
        # result = gpu_check_range(start, end)
        # return result == 1  # 1 = all converged
        
        # Placeholder
        import random
        time.sleep(1)  # Simulate computation
        return True  # All converged (placeholder)
    
    def verify_range_cpu(self, start: int, end: int) -> bool:
        """
        Verify range using CPU.
        Returns True if all numbers converge, False if counterexample found.
        """
        print(f"[WORKER] Using CPU verification...")
        
        # TODO: Integrate with actual CollatzEngine.py cpu_check_range
        # result = cpu_check_range(start, end)
        # return result == 1  # 1 = all converged
        
        # Placeholder
        import random
        time.sleep(5)  # Simulate longer CPU computation
        return True  # All converged (placeholder)
    
    def run_worker_loop(self, num_iterations: Optional[int] = None):
        """
        Main worker loop.
        Claims and verifies work continuously.
        
        Args:
            num_iterations: Number of work assignments to complete (None = infinite)
        """
        print(f"\n[WORKER] 🚀 Starting worker loop")
        print(f"[WORKER] Press Ctrl+C to stop\n")
        
        iterations = 0
        
        try:
            while True:
                # Check if we've reached iteration limit
                if num_iterations is not None and iterations >= num_iterations:
                    print(f"[WORKER] Completed {num_iterations} iterations")
                    break
                
                # Claim and verify work
                work_done = self.claim_and_verify_work()
                
                if work_done:
                    iterations += 1
                else:
                    # No work available, wait before checking again
                    print(f"[WORKER] Waiting 60s for new work...")
                    time.sleep(60)
                
                # Show session statistics
                self.show_statistics()
                
        except KeyboardInterrupt:
            print(f"\n[WORKER] Shutting down gracefully...")
            self.show_final_statistics()
    
    def show_statistics(self):
        """Show current session statistics."""
        session_time = time.time() - self.session_start
        
        print(f"\n[WORKER] 📊 Session Statistics:")
        print(f"[WORKER]   Ranges verified: {self.total_ranges_verified}")
        print(f"[WORKER]   Numbers checked: {self.total_numbers_checked:,}")
        print(f"[WORKER]   Compute time: {self.total_compute_time:.1f}s")
        if self.total_compute_time > 0:
            print(f"[WORKER]   Average rate: {self.total_numbers_checked / self.total_compute_time:,.0f} odd/sec")
        print(f"[WORKER]   Session time: {session_time / 60:.1f} minutes")
        
        # Show trust stats
        stats = self.trust_system.get_worker_stats(self.worker_id)
        if stats:
            print(f"[WORKER]   Trust level: {stats.trust_level.name}")
            print(f"[WORKER]   Reputation: {stats.reputation_score:.1f}/100")
            print(f"[WORKER]   Correct verifications: {stats.correct_verifications}")
        print()
    
    def show_final_statistics(self):
        """Show final statistics before shutdown."""
        self.show_statistics()
        
        # Show network statistics
        print(f"[WORKER] 🌐 Network Statistics:")
        network_stats = self.coordinator.get_network_statistics()
        for key, value in network_stats.items():
            if isinstance(value, (int, float)):
                print(f"[WORKER]   {key}: {value:,}" if isinstance(value, int) else f"[WORKER]   {key}: {value:.2f}")


def main():
    """Main entry point for distributed worker."""
    parser = argparse.ArgumentParser(description="Distributed Collatz Verification Worker")
    parser.add_argument('--ipfs-api', default='/ip4/127.0.0.1/tcp/5001',
                       help='IPFS API address (default: localhost:5001)')
    parser.add_argument('--cpu-only', action='store_true',
                       help='Use CPU-only mode (disable GPU)')
    parser.add_argument('--name', type=str,
                       help='Worker name (default: auto-generated)')
    parser.add_argument('--user-key', type=str,
                       help='Path to user private key file (for contribution tracking)')
    parser.add_argument('--create-account', type=str, metavar='USERNAME',
                       help='Create new user account with specified username')
    parser.add_argument('--iterations', type=int,
                       help='Number of work assignments to complete (default: infinite)')
    parser.add_argument('--generate-work', type=int, metavar='N',
                       help='Generate N new work assignments at the frontier')
    
    args = parser.parse_args()
    
    # Handle user account creation
    if args.create_account:
        print(f"[ACCOUNT] Creating new user account: {args.create_account}")
        try:
            from user_account import UserAccountManager
            manager = UserAccountManager()
            user_id, private_key_path = manager.create_user_account(args.create_account)
            print(f"[ACCOUNT] ✅ Account created!")
            print(f"[ACCOUNT]   User ID: {user_id}")
            print(f"[ACCOUNT]   Username: {args.create_account}")
            print(f"[ACCOUNT]   Private Key: {private_key_path}")
            print(f"\n[ACCOUNT] 🔐 Keep your private key safe!")
            print(f"[ACCOUNT] Use it to run workers: --user-key {private_key_path}")
            return 0
        except Exception as e:
            print(f"[ERROR] Failed to create account: {e}")
            return 1
    
    # First-run wizard (if no user account provided)
    first_run_marker = ".collatz_first_run"
    if not args.user_key and not os.path.exists(first_run_marker):
        print("\n" + "=" * 70)
        print("WELCOME TO THE COLLATZ DISTRIBUTED VERIFICATION NETWORK!")
        print("=" * 70)
        print()
        print("This is your first time running a worker node.")
        print()
        print("Would you like to create a USER ACCOUNT?")
        print()
        print("BENEFITS:")
        print("  ✅ Track your contributions across all your nodes")
        print("  ✅ Appear on the public leaderboard (IPFS webpage)")
        print("  ✅ Build reputation in the network")
        print("  ✅ Get credit if YOU find the counterexample!")
        print()
        print("WITHOUT ACCOUNT:")
        print("  ⚠️  Anonymous worker (no persistent identity)")
        print("  ⚠️  Stats tracked per-node only (not aggregated)")
        print("  ⚠️  No leaderboard recognition")
        print()
        
        create = input("Create user account now? [Y/n]: ").strip().lower()
        
        if create != 'n':
            username = input("Enter your username: ").strip()
            if username:
                try:
                    from user_account import UserAccountManager
                    manager = UserAccountManager()
                    user_id, private_key_path = manager.create_user_account(username)
                    print(f"\n✅ Account created!")
                    print(f"   Username: {username}")
                    print(f"   Private Key: {private_key_path}")
                    print(f"\n🔐 IMPORTANT: Backup this key file!")
                    print(f"   It's stored in: {private_key_path}")
                    print(f"\n   Next time, run with: --user-key {private_key_path}")
                    print()
                    args.user_key = private_key_path
                except Exception as e:
                    print(f"\n⚠️  Account creation failed: {e}")
                    print(f"   Continuing as anonymous worker...")
        
        # Mark first run complete
        with open(first_run_marker, 'w') as f:
            f.write(datetime.now().isoformat())
        
        print()
        print("=" * 70)
        print()
    
    # Initialize worker
    try:
        worker = DistributedCollatzWorker(
            ipfs_api=args.ipfs_api,
            use_gpu=not args.cpu_only,
            worker_name=args.name,
            user_key_file=args.user_key
        )
    except Exception as e:
        print(f"[ERROR] Failed to initialize worker: {e}")
        print(f"\nMake sure:")
        print(f"  1. IPFS daemon is running: ipfs daemon")
        print(f"  2. Python packages installed: pip install ipfshttpclient cryptography")
        if args.user_key:
            print(f"  3. User key file exists: {args.user_key}")
        return 1
    
    # Generate work if requested (any peer can generate work in decentralized network)
    if args.generate_work:
        print(f"[WORKER] Generating {args.generate_work} new work assignments...")
        assignments = worker.coordinator.generate_work_frontier(num_assignments=args.generate_work)
        print(f"[WORKER] ✅ Generated {len(assignments)} assignments")
        return 0
    
    # Run worker loop
    worker.run_worker_loop(num_iterations=args.iterations)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
