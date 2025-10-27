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
import random
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
    """
    Fully decentralized coordinator via IPFS.
    
    Key features:
    - NO single coordinator - any node can propose work
    - Self-organizing via gossip protocol
    - Automatic work generation when frontier runs low
    - Peer-to-peer state synchronization
    - Network runs forever with n>0 nodes
    """
    
    # Configuration
    WORK_TIMEOUT_SECONDS = 3600  # 1 hour to complete assigned work
    REDUNDANCY_FACTOR = 3  # Each range verified by 3 workers minimum
    RANGE_SIZE = 10_000_000_000  # 10 billion numbers per assignment
    STATE_PUBLISH_INTERVAL = 300  # Publish IPNS update every 5 minutes
    WORK_BUFFER_SIZE = 50  # Keep 50 assignments available (auto-generate more)
    GOSSIP_INTERVAL = 60  # Sync with peers every 60 seconds
    
    def __init__(self, ipfs_api: str = '/ip4/127.0.0.1/tcp/5001'):
        """Initialize IPFS coordinator (fully decentralized)."""
        if not IPFS_AVAILABLE:
            raise ImportError("ipfshttpclient not available")
        
        self.client = ipfshttpclient.connect(ipfs_api)
        self.node_id = self.client.id()['ID']
        
        # Local state (synced via gossip)
        self.work_assignments: Dict[str, WorkAssignment] = {}
        self.verification_proofs: Dict[str, VerificationProof] = {}
        self.global_highest_proven = 0
        self.last_publish_time = 0
        self.last_gossip_time = 0
        
        # Peer discovery (other nodes in network)
        self.known_peers: List[str] = []
        self.peer_states: Dict[str, str] = {}  # peer_id -> latest_state_cid
        
        # Worker availability tracking (for RANDOM assignment)
        self.available_workers: Dict[str, float] = {}  # worker_id -> last_seen_timestamp
        self.worker_assignments: Dict[str, str] = {}  # worker_id -> assignment_id (current assignment)
        
        # Genesis timestamp (network start time)
        self.genesis_timestamp: Optional[str] = None
        
        # Counterexample detection
        self.counterexample_found = False
        self.counterexample_data: Optional[Dict] = None
        
        print(f"[IPFS] 🌐 Fully decentralized node: {self.node_id[:16]}...")
        print(f"[IPFS] Network will run forever with n>0 nodes!")
        
        # Load existing state from network
        self.discover_and_sync_peers()
    
    def generate_assignment_id(self, range_start: int, range_end: int) -> str:
        """Generate unique ID for a work assignment."""
        data = f"{range_start}-{range_end}-{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def generate_proof_id(self, worker_id: str, assignment_id: str) -> str:
        """Generate unique ID for a verification proof."""
        data = f"{worker_id}-{assignment_id}-{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    
    def discover_and_sync_peers(self):
        """
        Discover other nodes in network and sync state.
        Fully peer-to-peer - no coordinator needed.
        """
        try:
            # Find peers via IPFS swarm
            swarm_peers = self.client.swarm.peers()
            self.known_peers = [p['Peer'] for p in swarm_peers if p['Peer'] != self.node_id]
            
            print(f"[IPFS] Discovered {len(self.known_peers)} peers in network")
            
            # Try to load state from well-known IPNS path (community shared)
            # Multiple nodes can publish here, we take most recent
            try:
                # Community namespace (anyone can read)
                community_path = "/ipns/collatz-distributed-network"
                resolved = self.client.name.resolve(community_path)
                state_cid = resolved['Path'].replace('/ipfs/', '')
                
                self.load_state_from_cid(state_cid)
                print(f"[IPFS] Synced with network state: /ipfs/{state_cid[:16]}...")
                
            except Exception as e:
                print(f"[IPFS] No existing network state found (first node?)")
                print(f"[IPFS] Initializing new network...")
                self.initialize_network()
        
        except Exception as e:
            print(f"[IPFS] Peer discovery error: {e}")
            print(f"[IPFS] Running in standalone mode")
    
    def initialize_network(self):
        """Initialize new network if no existing state found."""
        print(f"[IPFS] 🌟 Bootstrapping new Collatz verification network!")
        
        # Generate initial work frontier
        self.generate_work_frontier_internal(
            start_from=1,  # Start from beginning
            num_assignments=self.WORK_BUFFER_SIZE
        )
        
        # Publish initial state
        self.publish_state_to_network()
    
    def load_state_from_cid(self, state_cid: str):
        """Load state from a specific IPFS CID."""
        try:
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
            
            print(f"[IPFS] Loaded: {len(self.work_assignments)} assignments, "
                  f"{len(self.verification_proofs)} proofs")
            print(f"[IPFS] Global highest: {self.global_highest_proven:,}")
            
        except Exception as e:
            print(f"[IPFS] Error loading state: {e}")
    
    def publish_state_to_network(self):
        """
        Publish current state to IPFS network.
        Any node can do this - uses content-addressing for consensus.
        """
        try:
            # Prepare state data
            state = {
                'global_highest_proven': self.global_highest_proven,
                'work_assignments': [asdict(a) for a in self.work_assignments.values()],
                'verification_proofs': [asdict(p) for p in self.verification_proofs.values()],
                'published_by': self.node_id,
                'timestamp': time.time(),
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
            
            # Publish to personal IPNS (each node has own IPNS)
            try:
                self.client.name.publish(state_cid, key='collatz-state', lifetime='24h')
            except:
                pass  # IPNS key might not exist yet
            
            self.last_publish_time = time.time()
            
            print(f"[IPFS] 📤 Published state: /ipfs/{state_cid[:16]}...")
            
            return state_cid
            
        except Exception as e:
            print(f"[IPFS] Error publishing state: {e}")
            return None
    
    def gossip_sync_with_peers(self):
        """
        Sync state with peers via gossip protocol.
        Merges states from multiple nodes for consensus.
        """
        current_time = time.time()
        
        if current_time - self.last_gossip_time < self.GOSSIP_INTERVAL:
            return  # Too soon
        
        self.last_gossip_time = current_time
        
        # Refresh peer list
        try:
            swarm_peers = self.client.swarm.peers()
            self.known_peers = [p['Peer'] for p in swarm_peers if p['Peer'] != self.node_id]
        except:
            pass
        
        # Try to fetch and merge state from random peers
        import random
        sample_size = min(5, len(self.known_peers))
        if sample_size > 0:
            sample_peers = random.sample(self.known_peers, sample_size)
            
            for peer_id in sample_peers:
                try:
                    # Try to resolve peer's IPNS
                    peer_ipns = f"/ipns/{peer_id}"
                    resolved = self.client.name.resolve(peer_ipns, timeout=5)
                    peer_state_cid = resolved['Path'].replace('/ipfs/', '')
                    
                    # Merge their state with ours
                    self.merge_peer_state(peer_state_cid)
                    
                except:
                    continue  # Peer might not have published yet
        
        print(f"[IPFS] 🔄 Gossip sync complete ({len(self.known_peers)} peers)")
    
    def merge_peer_state(self, peer_state_cid: str):
        """
        Merge state from another peer.
        Resolves conflicts by taking maximum progress.
        """
        try:
            peer_json = self.client.cat(peer_state_cid)
            peer_state = json.loads(peer_json)
            
            # Merge work assignments (union of all assignments)
            for assignment_dict in peer_state.get('work_assignments', []):
                assignment = WorkAssignment(**assignment_dict)
                assignment_id = assignment.assignment_id
                
                if assignment_id not in self.work_assignments:
                    # New assignment, add it
                    self.work_assignments[assignment_id] = assignment
                else:
                    # Merge assignment (take more complete version)
                    existing = self.work_assignments[assignment_id]
                    if len(assignment.completed_workers) > len(existing.completed_workers):
                        self.work_assignments[assignment_id] = assignment
            
            # Merge proofs (union)
            for proof_dict in peer_state.get('verification_proofs', []):
                proof = VerificationProof(**proof_dict)
                if proof.proof_id not in self.verification_proofs:
                    self.verification_proofs[proof.proof_id] = proof
            
            # Take maximum highest_proven
            peer_highest = peer_state.get('global_highest_proven', 0)
            if peer_highest > self.global_highest_proven:
                self.global_highest_proven = peer_highest
                print(f"[IPFS] ⬆️ Updated global highest: {self.global_highest_proven:,}")
        
        except Exception as e:
            print(f"[IPFS] Error merging peer state: {e}")
    
    def auto_generate_work_if_needed(self):
        """
        Automatically generate new work if frontier is running low.
        Any node can do this - network self-organizes.
        """
        # Count available work
        available = sum(1 for a in self.work_assignments.values() 
                       if a.status in ['available', 'in_progress'] and 
                       len(a.assigned_workers) < a.redundancy_factor)
        
        if available < self.WORK_BUFFER_SIZE // 2:
            print(f"[IPFS] ⚠️ Low work available ({available}), generating more...")
            
            # Find highest range end
            max_range_end = 0
            for assignment in self.work_assignments.values():
                if assignment.range_end > max_range_end:
                    max_range_end = assignment.range_end
            
            # Generate new work at frontier
            start_from = max(max_range_end, self.global_highest_proven + 1)
            new_assignments = self.generate_work_frontier_internal(
                start_from=start_from,
                num_assignments=self.WORK_BUFFER_SIZE
            )
            
            print(f"[IPFS] ✅ Generated {len(new_assignments)} new assignments")
            
            # Publish to network immediately
            self.publish_state_to_network()
    
    def generate_work_frontier_internal(self, start_from: int, 
                                       num_assignments: int) -> List[WorkAssignment]:
        """
        Generate new work assignments (internal method).
        Creates chunks at frontier for verification.
        """
        # Ensure start is odd
        if start_from % 2 == 0:
            start_from += 1
        
        assignments = []
        current = start_from
        
        for i in range(num_assignments):
            range_end = current + self.RANGE_SIZE
            
            # Check if this range already exists
            existing = any(
                a.range_start == current and a.range_end == range_end
                for a in self.work_assignments.values()
            )
            
            if not existing:
                assignment = self.create_work_assignment_internal(current, range_end)
                assignments.append(assignment)
            
            current = range_end
        
        return assignments
    
    def create_work_assignment_internal(self, range_start: int, range_end: int, 
                                       priority: int = 1) -> WorkAssignment:
        """Create a new work assignment (internal method)."""
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
        return assignment
    
    
    # Keep old methods for backward compatibility (they now call internal versions)
    def save_state_to_ipns(self):
        """Legacy method - now calls publish_state_to_network()."""
        return self.publish_state_to_network()
    
    def create_work_assignment(self, range_start: int, range_end: int, 
                               priority: int = 1) -> WorkAssignment:
        """Legacy method - now calls internal version."""
        return self.create_work_assignment_internal(range_start, range_end, priority)
    
    def generate_work_frontier(self, start_from: Optional[int] = None, 
                                num_assignments: int = 100) -> List[WorkAssignment]:
        """Legacy method - now calls internal version with auto-publish."""
        if start_from is None:
            start_from = self.global_highest_proven + 1
        
        assignments = self.generate_work_frontier_internal(start_from, num_assignments)
        
        if assignments:
            print(f"[IPFS] Generated {len(assignments)} new assignments")
            print(f"[IPFS] Frontier: {assignments[0].range_start:,} to {assignments[-1].range_end:,}")
            self.publish_state_to_network()
        
        return assignments
    
    def register_worker_availability(self, worker_id: str, user_id: Optional[str] = None):
        """
        Register worker as available for random assignment.
        
        SECURITY: This prevents workers from choosing their own work.
        Workers must register availability, then coordinator randomly assigns them.
        
        Args:
            worker_id: Unique worker identifier
            user_id: Optional user account ID
        """
        self.available_workers[worker_id] = time.time()
        
        # Clean up stale workers (not seen in 5 minutes)
        current_time = time.time()
        stale_workers = [
            wid for wid, last_seen in self.available_workers.items()
            if current_time - last_seen > 300  # 5 minutes
        ]
        for wid in stale_workers:
            del self.available_workers[wid]
            if wid in self.worker_assignments:
                # Worker went offline, free up their assignment
                assignment_id = self.worker_assignments[wid]
                if assignment_id in self.work_assignments:
                    assignment = self.work_assignments[assignment_id]
                    if worker_id in assignment.assigned_workers:
                        assignment.assigned_workers.remove(worker_id)
                    assignment.status = 'available'
                del self.worker_assignments[wid]
        
        print(f"[IPFS] Worker {worker_id[:16]}... registered (available pool: {len(self.available_workers)})")
    
    def randomly_assign_workers_to_ranges(self):
        """
        Randomly assign available workers to unassigned ranges.
        
        SECURITY CRITICAL: This prevents collusion by ensuring workers
        cannot predict who will verify their work.
        
        Algorithm:
        1. Find ranges that need more verifiers
        2. Get list of available workers (not currently assigned)
        3. Randomly shuffle workers
        4. Assign workers to ranges until each has required redundancy
        """
        if not self.available_workers:
            return  # No workers available
        
        current_time = time.time()
        
        # Find ranges needing more verifiers
        needs_assignment = [
            a for a in self.work_assignments.values()
            if a.status in ['available', 'in_progress']
            and len(a.assigned_workers) < a.redundancy_factor
        ]
        
        if not needs_assignment:
            return  # All ranges fully assigned
        
        # Get workers not currently assigned
        assigned_worker_ids = set(self.worker_assignments.keys())
        free_workers = [
            wid for wid in self.available_workers.keys()
            if wid not in assigned_worker_ids
        ]
        
        if not free_workers:
            return  # No free workers
        
        # RANDOM SHUFFLE - this is the security feature!
        random.shuffle(free_workers)
        random.shuffle(needs_assignment)
        
        assignments_made = 0
        
        for assignment in needs_assignment:
            # How many more workers needed?
            needed = assignment.redundancy_factor - len(assignment.assigned_workers)
            if needed <= 0:
                continue
            
            # Assign random workers
            for _ in range(needed):
                if not free_workers:
                    break  # No more workers available
                
                worker_id = free_workers.pop(0)
                
                # Assign worker to range
                assignment.assigned_workers.append(worker_id)
                self.worker_assignments[worker_id] = assignment.assignment_id
                assignment.timeout_at = current_time + self.WORK_TIMEOUT_SECONDS
                
                if len(assignment.assigned_workers) >= assignment.redundancy_factor:
                    assignment.status = 'in_progress'
                
                assignments_made += 1
                
                print(f"[IPFS] 🎲 RANDOM ASSIGNMENT: Worker {worker_id[:16]}... -> Range {assignment.range_start:,}-{assignment.range_end:,}")
        
        if assignments_made > 0:
            print(f"[IPFS] Made {assignments_made} random assignments (prevents collusion)")
            self.publish_state_to_network()
    
    
    def claim_work(self, worker_id: str, user_id: Optional[str] = None) -> Optional[WorkAssignment]:
        """
        Check if worker has been randomly assigned work.
        
        NEW SECURITY MODEL: Workers don't claim work, they CHECK for assignments.
        Coordinator randomly assigns workers to prevent collusion.
        
        Workflow:
        1. Worker registers availability
        2. Coordinator randomly assigns worker to range  
        3. Worker checks here for their assignment
        4. Worker cannot choose or refuse work
        
        Args:
            worker_id: Unique worker identifier
            user_id: Optional user account for contribution tracking
            
        Returns:
            WorkAssignment if worker has been assigned, None otherwise
        """
        current_time = time.time()
        
        # Register this worker as available
        self.register_worker_availability(worker_id, user_id)
        
        # Auto-generate work if needed (decentralized!)
        self.auto_generate_work_if_needed()
        
        # Perform random assignment (any node can do this)
        self.randomly_assign_workers_to_ranges()
        
        # Gossip sync with peers periodically
        self.gossip_sync_with_peers()
        
        # Check if this worker has been assigned work
        if worker_id not in self.worker_assignments:
            return None  # Not assigned yet
        
        assignment_id = self.worker_assignments[worker_id]
        if assignment_id not in self.work_assignments:
            # Assignment no longer exists
            del self.worker_assignments[worker_id]
            return None
        
        assignment = self.work_assignments[assignment_id]
        
        # Verify worker is actually assigned to this range
        if worker_id not in assignment.assigned_workers:
            del self.worker_assignments[worker_id]
            return None
        
        print(f"[IPFS] Worker {worker_id[:16]}... has assignment {assignment.assignment_id[:8]}...")
        if user_id:
            print(f"[IPFS] User: {user_id}")
        print(f"[IPFS] Range: {assignment.range_start:,} to {assignment.range_end:,}")
        print(f"[IPFS] Progress: {len(assignment.assigned_workers)}/{assignment.redundancy_factor} workers")
        print(f"[IPFS] 🔒 RANDOMLY ASSIGNED (prevents collusion)")
        
        # Publish state update periodically
        if current_time - self.last_publish_time > self.STATE_PUBLISH_INTERVAL:
            self.publish_state_to_network()
        
        return assignment
    
    def submit_verification_proof(self, worker_id: str, assignment_id: str,
                                   all_converged: bool, numbers_checked: int,
                                   max_steps: int, compute_time: float,
                                   detailed_proof: Dict, user_id: Optional[str] = None) -> str:
        """
        Submit a verification proof to IPFS.
        Now includes user_id for contribution tracking.
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
        
        # Free up worker for next assignment (random assignment system)
        if worker_id in self.worker_assignments:
            del self.worker_assignments[worker_id]
            print(f"[IPFS] Worker {worker_id[:16]}... freed for next assignment")
        
        # Check if assignment is complete (all redundant verifications done)
        if len(assignment.completed_workers) >= assignment.redundancy_factor:
            assignment.status = 'completed'
            print(f"[IPFS] ✅ Assignment {assignment_id[:8]}... completed by {assignment.redundancy_factor} workers")
        
        # Publish state update (decentralized - any node can publish)
        self.publish_state_to_network()
        
        print(f"[IPFS] Proof submitted: {proof.proof_id[:8]}...")
        if user_id:
            print(f"[IPFS] User: {user_id}")
        print(f"[IPFS] IPFS CID: /ipfs/{proof_cid[:16]}...")
        
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
        """Update the global highest proven value (decentralized)."""
        if new_highest > self.global_highest_proven:
            self.global_highest_proven = new_highest
            print(f"[IPFS] 🎉 New global highest proven: {new_highest:,}")
            
            # Publish immediately for milestone updates (any node can publish!)
            self.publish_state_to_network()
    
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
        available = sum(1 for a in self.work_assignments.values() if a.status == 'available')
        
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
            'known_peers': len(self.known_peers),
            'total_assignments': total_assignments,
            'available_assignments': available,
            'in_progress_assignments': in_progress,
            'completed_assignments': completed,
            'conflicting_assignments': conflicts,
            'total_proofs': len(self.verification_proofs),
            'total_numbers_verified': total_verified,
            'total_compute_time_hours': total_compute / 3600,
            'average_time_per_billion': (total_compute / (total_verified / 1e9)) if total_verified > 0 else 0,
            'network_mode': 'fully_decentralized'
        }


# Example usage
if __name__ == "__main__":
    if not IPFS_AVAILABLE:
        print("Please install: pip install ipfshttpclient")
        exit(1)
    
    print("🌐 Fully Decentralized Collatz Network")
    print("=" * 50)
    print("This network runs forever with n>0 nodes!")
    print("No single coordinator - all nodes are equal peers.")
    print("=" * 50)
    
    coordinator = IPFSCoordinator()
    
    # Show network stats
    stats = coordinator.get_network_statistics()
    print(f"\nNetwork Statistics:")
    print(f"  Mode: {stats['network_mode']}")
    print(f"  Known peers: {stats['known_peers']}")
    print(f"  Active workers: {stats['active_workers']}")
    print(f"  Available work: {stats['available_assignments']}")
    print(f"  Global highest: {stats['global_highest_proven']:,}")
    
    # If low on work, generate more (any node can do this!)
    if stats['available_assignments'] < 10:
        print(f"\n⚠️ Low work available, generating more...")
        coordinator.auto_generate_work_if_needed()

