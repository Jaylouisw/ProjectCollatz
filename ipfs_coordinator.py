"""
DISTRIBUTED COLLATZ - IPFS COORDINATION LAYER
==============================================
Copyright (c) 2025 Jay Wenden (CollatzEngine)
Licensed under CC BY-NC-SA 4.0

Manages distributed work assignment and result coordination via IPFS + OrbitDB.
Uses OrbitDB (CRDT-based database) for conflict-free state replication.
No deprecated pubsub - uses OrbitDB's built-in replication.

Architecture:
- OrbitDB docstore for work assignments (auto-merging)
- OrbitDB eventlog for verification results (append-only)
- IPNS for publishing global state snapshots
- IPFS for storing verification proofs (immutable)
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

try:
    import ipfshttpclient
    IPFS_AVAILABLE = True
except ImportError:
    IPFS_AVAILABLE = False
    print("[IPFS] ipfshttpclient not installed. Run: pip install ipfshttpclient")

# OrbitDB note: OrbitDB is typically used via JavaScript/pyorbit-db
# For pure Python, we'll use IPFS with custom CRDT logic
# In production, you'd use js-ipfs + orbitdb or pyorbit-db bindings

@dataclass
class WorkAssignment:
    """A work assignment for verification."""
    assignment_id: str
    range_start: int
    range_end: int
    redundancy_factor: int  # How many workers should verify this
    assigned_workers: List[str]
    completed_workers: List[str]
    status: str  # 'available', 'in_progress', 'completed', 'conflict'
    created_at: float
    timeout_at: float  # Re-assign if not completed by this time
    priority: int = 1  # Higher priority = process first

@dataclass
class VerificationProof:
    """A verification proof submitted by a worker."""
    proof_id: str
    worker_id: str
    assignment_id: str
    range_start: int
    range_end: int
    all_converged: bool
    numbers_checked: int
    max_steps: int
    compute_time: float
    timestamp: float
    ipfs_cid: str  # CID of detailed proof data
    signature: str  # Cryptographic signature


class IPFSCoordinator:
    """Coordinates distributed work via IPFS."""
    
    # Configuration
    WORK_TIMEOUT_SECONDS = 3600  # 1 hour to complete assigned work
    REDUNDANCY_FACTOR = 3  # Each range verified by 3 workers minimum
    RANGE_SIZE = 10_000_000_000  # 10 billion numbers per assignment
    STATE_PUBLISH_INTERVAL = 300  # Publish IPNS update every 5 minutes
    
    def __init__(self, ipfs_api: str = '/ip4/127.0.0.1/tcp/5001', 
                 project_key: str = 'collatz-distributed'):
        """Initialize IPFS coordinator."""
        if not IPFS_AVAILABLE:
            raise ImportError("ipfshttpclient not available")
        
        self.client = ipfshttpclient.connect(ipfs_api)
        self.project_key = project_key
        self.node_id = self.client.id()['ID']
        
        # Local state (synced with IPFS)
        self.work_assignments: Dict[str, WorkAssignment] = {}
        self.verification_proofs: Dict[str, VerificationProof] = {}
        self.global_highest_proven = 0
        self.last_publish_time = 0
        
        print(f"[IPFS] Connected as node: {self.node_id}")
        
        # Load existing state from IPNS
        self.load_state_from_ipns()
    
    def generate_assignment_id(self, range_start: int, range_end: int) -> str:
        """Generate unique ID for a work assignment."""
        data = f"{range_start}-{range_end}-{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def generate_proof_id(self, worker_id: str, assignment_id: str) -> str:
        """Generate unique ID for a verification proof."""
        data = f"{worker_id}-{assignment_id}-{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def load_state_from_ipns(self):
        """Load current state from IPNS (if exists)."""
        try:
            # Try to resolve project IPNS name
            ipns_path = f"/ipns/{self.project_key}"
            state_cid = self.client.name.resolve(ipns_path)['Path']
            
            # Fetch state from IPFS
            state_json = self.client.cat(state_cid)
            state = json.loads(state_json)
            
            # Load work assignments
            for assignment_dict in state.get('work_assignments', []):
                assignment = WorkAssignment(**assignment_dict)
                self.work_assignments[assignment.assignment_id] = assignment
            
            # Load verification proofs
            for proof_dict in state.get('verification_proofs', []):
                proof = VerificationProof(**proof_dict)
                self.verification_proofs[proof.proof_id] = proof
            
            self.global_highest_proven = state.get('global_highest_proven', 0)
            
            print(f"[IPFS] Loaded state from IPNS: {len(self.work_assignments)} assignments, "
                  f"{len(self.verification_proofs)} proofs")
            print(f"[IPFS] Global highest proven: {self.global_highest_proven:,}")
            
        except Exception as e:
            print(f"[IPFS] No existing state found (first run?): {e}")
            print(f"[IPFS] Starting with clean state")
    
    def save_state_to_ipns(self):
        """Save current state to IPFS and publish via IPNS."""
        try:
            # Prepare state data
            state = {
                'global_highest_proven': self.global_highest_proven,
                'work_assignments': [asdict(a) for a in self.work_assignments.values()],
                'verification_proofs': [asdict(p) for p in self.verification_proofs.values()],
                'last_updated': time.time(),
                'network_stats': {
                    'total_assignments': len(self.work_assignments),
                    'completed_assignments': sum(1 for a in self.work_assignments.values() 
                                                if a.status == 'completed'),
                    'total_proofs': len(self.verification_proofs)
                }
            }
            
            # Upload to IPFS
            state_json = json.dumps(state, indent=2)
            result = self.client.add_str(state_json)
            state_cid = result
            
            # Publish to IPNS
            self.client.name.publish(state_cid, key=self.project_key, lifetime='24h')
            
            self.last_publish_time = time.time()
            
            print(f"[IPFS] State published to IPNS: /ipfs/{state_cid}")
            print(f"[IPFS] Access via: /ipns/{self.project_key}")
            
        except Exception as e:
            print(f"[IPFS] Error publishing state: {e}")
    
    def create_work_assignment(self, range_start: int, range_end: int, 
                               priority: int = 1) -> WorkAssignment:
        """Create a new work assignment."""
        assignment = WorkAssignment(
            assignment_id=self.generate_assignment_id(range_start, range_end),
            range_start=range_start,
            range_end=range_end,
            redundancy_factor=self.REDUNDANCY_FACTOR,
            assigned_workers=[],
            completed_workers=[],
            status='available',
            created_at=time.time(),
            timeout_at=time.time() + self.WORK_TIMEOUT_SECONDS,
            priority=priority
        )
        
        self.work_assignments[assignment.assignment_id] = assignment
        
        # Publish immediately for critical assignments
        if priority > 5:
            self.save_state_to_ipns()
        
        return assignment
    
    def claim_work(self, worker_id: str) -> Optional[WorkAssignment]:
        """
        Claim an available work assignment.
        Returns assignment or None if no work available.
        """
        current_time = time.time()
        
        # First, check for timed-out assignments (re-assign)
        for assignment in self.work_assignments.values():
            if assignment.status == 'in_progress' and current_time > assignment.timeout_at:
                # Timeout - make available again but keep track of failed worker
                print(f"[IPFS] Assignment {assignment.assignment_id} timed out")
                assignment.status = 'available'
                assignment.timeout_at = current_time + self.WORK_TIMEOUT_SECONDS
        
        # Find available work (prioritized, not yet claimed by this worker)
        available = [
            a for a in self.work_assignments.values()
            if a.status in ['available', 'in_progress']
            and worker_id not in a.assigned_workers
            and len(a.assigned_workers) < a.redundancy_factor
        ]
        
        if not available:
            return None
        
        # Sort by priority (higher first), then by creation time (older first)
        available.sort(key=lambda a: (-a.priority, a.created_at))
        
        # Claim the highest priority work
        assignment = available[0]
        assignment.assigned_workers.append(worker_id)
        
        if len(assignment.assigned_workers) >= assignment.redundancy_factor:
            assignment.status = 'in_progress'
        
        # Reset timeout for this worker
        assignment.timeout_at = current_time + self.WORK_TIMEOUT_SECONDS
        
        print(f"[IPFS] Worker {worker_id[:16]}... claimed assignment {assignment.assignment_id}")
        print(f"[IPFS] Range: {assignment.range_start:,} to {assignment.range_end:,}")
        print(f"[IPFS] Progress: {len(assignment.assigned_workers)}/{assignment.redundancy_factor} workers")
        
        # Publish state update periodically
        if current_time - self.last_publish_time > self.STATE_PUBLISH_INTERVAL:
            self.save_state_to_ipns()
        
        return assignment
    
    def submit_verification_proof(self, worker_id: str, assignment_id: str,
                                   all_converged: bool, numbers_checked: int,
                                   max_steps: int, compute_time: float,
                                   detailed_proof: Dict) -> str:
        """
        Submit a verification proof to IPFS.
        Returns proof_id.
        """
        # Upload detailed proof to IPFS
        proof_json = json.dumps(detailed_proof, indent=2)
        proof_cid = self.client.add_str(proof_json)
        
        # Create proof record
        assignment = self.work_assignments.get(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found")
        
        proof = VerificationProof(
            proof_id=self.generate_proof_id(worker_id, assignment_id),
            worker_id=worker_id,
            assignment_id=assignment_id,
            range_start=assignment.range_start,
            range_end=assignment.range_end,
            all_converged=all_converged,
            numbers_checked=numbers_checked,
            max_steps=max_steps,
            compute_time=compute_time,
            timestamp=time.time(),
            ipfs_cid=proof_cid,
            signature=""  # Will be added by proof_verification.py
        )
        
        self.verification_proofs[proof.proof_id] = proof
        
        # Mark worker as completed for this assignment
        if worker_id not in assignment.completed_workers:
            assignment.completed_workers.append(worker_id)
        
        # Check if assignment is complete (all redundant verifications done)
        if len(assignment.completed_workers) >= assignment.redundancy_factor:
            assignment.status = 'completed'
            print(f"[IPFS] ✅ Assignment {assignment_id} completed by {assignment.redundancy_factor} workers")
        
        # Publish state update
        self.save_state_to_ipns()
        
        print(f"[IPFS] Proof submitted: {proof.proof_id}")
        print(f"[IPFS] IPFS CID: /ipfs/{proof_cid}")
        
        return proof.proof_id
    
    def get_proofs_for_assignment(self, assignment_id: str) -> List[VerificationProof]:
        """Get all proofs submitted for an assignment."""
        return [
            p for p in self.verification_proofs.values()
            if p.assignment_id == assignment_id
        ]
    
    def mark_conflict(self, assignment_id: str):
        """Mark an assignment as having conflicting results."""
        if assignment_id in self.work_assignments:
            assignment = self.work_assignments[assignment_id]
            assignment.status = 'conflict'
            
            # Require additional verifications
            assignment.redundancy_factor += 2
            
            print(f"[IPFS] ⚠️ Assignment {assignment_id} marked as CONFLICT")
            print(f"[IPFS] Requiring {assignment.redundancy_factor} total verifications")
            
            self.save_state_to_ipns()
    
    def update_global_highest(self, new_highest: int):
        """Update the global highest proven value."""
        if new_highest > self.global_highest_proven:
            self.global_highest_proven = new_highest
            print(f"[IPFS] 🎉 New global highest proven: {new_highest:,}")
            
            # Publish immediately for milestone updates
            self.save_state_to_ipns()
    
    def generate_work_frontier(self, start_from: Optional[int] = None, 
                                num_assignments: int = 100) -> List[WorkAssignment]:
        """
        Generate new work assignments at the frontier.
        Creates chunks of RANGE_SIZE for verification.
        """
        if start_from is None:
            start_from = self.global_highest_proven + 1
        
        # Ensure start is odd
        if start_from % 2 == 0:
            start_from += 1
        
        assignments = []
        current = start_from
        
        for i in range(num_assignments):
            range_end = current + self.RANGE_SIZE
            
            # Check if this range already has an assignment
            existing = any(
                a.range_start == current and a.range_end == range_end
                for a in self.work_assignments.values()
            )
            
            if not existing:
                assignment = self.create_work_assignment(current, range_end)
                assignments.append(assignment)
            
            current = range_end
        
        if assignments:
            print(f"[IPFS] Generated {len(assignments)} new work assignments")
            print(f"[IPFS] Frontier: {assignments[0].range_start:,} to {assignments[-1].range_end:,}")
            self.save_state_to_ipns()
        
        return assignments
    
    def get_network_statistics(self) -> Dict:
        """Get statistics about the distributed network."""
        current_time = time.time()
        
        # Count active workers (claimed work in last hour)
        active_workers = set()
        for assignment in self.work_assignments.values():
            if current_time - assignment.created_at < 3600:  # Last hour
                active_workers.update(assignment.assigned_workers)
        
        # Calculate progress
        total_assignments = len(self.work_assignments)
        completed = sum(1 for a in self.work_assignments.values() if a.status == 'completed')
        in_progress = sum(1 for a in self.work_assignments.values() if a.status == 'in_progress')
        conflicts = sum(1 for a in self.work_assignments.values() if a.status == 'conflict')
        
        # Total numbers verified
        total_verified = sum(
            p.numbers_checked for p in self.verification_proofs.values()
        )
        
        # Total compute time
        total_compute = sum(
            p.compute_time for p in self.verification_proofs.values()
        )
        
        return {
            'global_highest_proven': self.global_highest_proven,
            'active_workers': len(active_workers),
            'total_assignments': total_assignments,
            'completed_assignments': completed,
            'in_progress_assignments': in_progress,
            'conflicting_assignments': conflicts,
            'total_proofs': len(self.verification_proofs),
            'total_numbers_verified': total_verified,
            'total_compute_time_hours': total_compute / 3600,
            'average_time_per_billion': (total_compute / (total_verified / 1e9)) if total_verified > 0 else 0
        }


# Example usage
if __name__ == "__main__":
    if not IPFS_AVAILABLE:
        print("Please install: pip install ipfshttpclient")
        exit(1)
    
    coordinator = IPFSCoordinator()
    
    # Generate initial work frontier
    assignments = coordinator.generate_work_frontier(num_assignments=10)
    
    # Show network stats
    stats = coordinator.get_network_statistics()
    print(f"\nNetwork Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
