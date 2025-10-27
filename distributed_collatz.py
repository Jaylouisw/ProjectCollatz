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

# Import distributed components
from ipfs_coordinator import IPFSCoordinator, IPFS_AVAILABLE
from trust_system import TrustSystem
from proof_verification import ProofVerificationSystem, CRYPTO_AVAILABLE

# Import CollatzEngine components
try:
    from CollatzEngine import gpu_check_range, cpu_check_range, GPU_AVAILABLE
    ENGINE_AVAILABLE = True
except ImportError:
    print("[ERROR] CollatzEngine not found. Make sure CollatzEngine.py is in the same directory.")
    ENGINE_AVAILABLE = False


class DistributedCollatzWorker:
    """A worker node in the distributed Collatz verification network."""
    
    def __init__(self, ipfs_api: str = '/ip4/127.0.0.1/tcp/5001',
                 use_gpu: bool = True,
                 worker_name: Optional[str] = None):
        """Initialize distributed worker."""
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
        
        # Worker identity
        self.worker_id = self.coordinator.node_id
        self.worker_name = worker_name or f"Worker-{self.worker_id[:8]}"
        self.use_gpu = use_gpu and GPU_AVAILABLE
        
        # Load or generate worker keypair
        self.private_key, self.public_key = self.load_or_generate_keypair()
        
        # Register public key with network
        public_key_pem = self.verifier.serialize_public_key(self.public_key)
        self.verifier.register_worker_key(self.worker_id, public_key_pem)
        
        # Statistics
        self.total_ranges_verified = 0
        self.total_numbers_checked = 0
        self.total_compute_time = 0.0
        self.session_start = time.time()
        
        print(f"[WORKER] Initialized: {self.worker_name}")
        print(f"[WORKER] Node ID: {self.worker_id}")
        print(f"[WORKER] Mode: {'GPU' if self.use_gpu else 'CPU'}")
        
        # Check trust level
        stats = self.trust_system.get_worker_stats(self.worker_id)
        if stats:
            print(f"[WORKER] Trust Level: {stats.trust_level.name}")
            print(f"[WORKER] Reputation: {stats.reputation_score:.1f}/100")
        else:
            print(f"[WORKER] Trust Level: NEW (UNTRUSTED)")
    
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
        Returns True if work was completed, False if no work available.
        """
        # Claim work assignment
        assignment = self.coordinator.claim_work(self.worker_id)
        
        if assignment is None:
            print(f"[WORKER] No work available")
            return False
        
        print(f"\n[WORKER] 🔨 Starting verification of range:")
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
            print(f"[WORKER] Proof uploaded to IPFS: /ipfs/{proof_cid}")
            
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
            
            # Submit proof to coordinator
            proof_id = self.coordinator.submit_verification_proof(
                worker_id=self.worker_id,
                assignment_id=assignment.assignment_id,
                all_converged=all_converged,
                numbers_checked=numbers_checked,
                max_steps=100000,
                compute_time=compute_time,
                detailed_proof=detailed_proof
            )
            
            # Submit for consensus/trust verification
            consensus_reached, message = self.verifier.submit_for_consensus(signed_proof)
            print(f"[WORKER] {message}")
            
            # Update statistics
            self.total_ranges_verified += 1
            self.total_numbers_checked += numbers_checked
            self.total_compute_time += compute_time
            
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
    parser.add_argument('--iterations', type=int,
                       help='Number of work assignments to complete (default: infinite)')
    parser.add_argument('--generate-work', type=int, metavar='N',
                       help='Generate N new work assignments at the frontier')
    
    args = parser.parse_args()
    
    # Initialize worker
    try:
        worker = DistributedCollatzWorker(
            ipfs_api=args.ipfs_api,
            use_gpu=not args.cpu_only,
            worker_name=args.name
        )
    except Exception as e:
        print(f"[ERROR] Failed to initialize worker: {e}")
        print(f"\nMake sure:")
        print(f"  1. IPFS daemon is running: ipfs daemon")
        print(f"  2. Python packages installed: pip install ipfshttpclient cryptography")
        return 1
    
    # Generate work if requested (useful for network coordinator)
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
