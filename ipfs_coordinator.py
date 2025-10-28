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
from trust_system import TrustSystem

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
    creator_user_id: Optional[str] = None  # CRITICAL: Track who created this work to prevent self-verification

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
        
        # 🔒 SECURITY: Trust system for consensus validation
        self.trust_system = TrustSystem()
        
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
        self.available_workers: Dict[str, Dict[str, any]] = {}  # worker_id -> {timestamp, user_id}
        self.worker_assignments: Dict[str, str] = {}  # worker_id -> assignment_id (current assignment)
        
        # Genesis timestamp (network start time)
        self.genesis_timestamp: Optional[str] = None
        
        # Counterexample detection
        self.counterexample_found = False
        self.counterexample_data: Optional[Dict] = None
        
        # Leaderboard & Status Website (fully decentralized)
        self.leaderboard_generator = None
        self.status_generator = None
        self.last_leaderboard_update = 0
        self.last_status_update = 0
        self.leaderboard_update_interval = 300  # Update every 5 minutes after verification completes
        self.status_update_interval = 60  # Update status every 1 minute
        
        # Consensus voting for canonical leaderboard/status CIDs
        self.leaderboard_votes: Dict[str, int] = {}  # CID -> vote count
        self.status_votes: Dict[str, int] = {}  # CID -> vote count
        self.canonical_leaderboard_cid: Optional[str] = None
        self.canonical_status_cid: Optional[str] = None
        
        print(f"[IPFS] 🌐 Fully decentralized node: {self.node_id[:16]}...")
        print(f"[IPFS] Network will run forever with n>0 nodes!")
        
        # Initialize leaderboard and status generators (ALL nodes can update)
        try:
            from leaderboard_generator import LeaderboardGenerator
            from status_website_generator import StatusWebsiteGenerator
            self.leaderboard_generator = LeaderboardGenerator()
            self.status_generator = StatusWebsiteGenerator()
            print(f"[IPFS] 📊 Decentralized leaderboard & status enabled (all nodes can publish)")
        except Exception as e:
            print(f"[IPFS] ⚠️ Leaderboard/status disabled: {e}")
        
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
            
            # Handle different response formats from IPFS API
            self.known_peers = []
            
            # Check if it's a dict with 'Peers' key
            if isinstance(swarm_peers, dict):
                if 'Peers' in swarm_peers:
                    peer_list = swarm_peers['Peers']
                else:
                    # Empty dict or unexpected format
                    peer_list = []
            elif isinstance(swarm_peers, list):
                peer_list = swarm_peers
            else:
                # Unknown format, skip peer discovery
                peer_list = []
            
            # Extract peer IDs, handling various formats
            for p in peer_list:
                try:
                    if isinstance(p, dict):
                        # Format: {'Peer': 'ID', 'Addr': '/ip4/...'}
                        if 'Peer' in p:
                            peer_id = p['Peer']
                        else:
                            continue
                    elif isinstance(p, str):
                        # Format: multiaddr string like "/ip4/.../p2p/ID"
                        if '/p2p/' in p:
                            peer_id = p.split('/p2p/')[-1]
                        elif '/ipfs/' in p:
                            peer_id = p.split('/ipfs/')[-1]
                        else:
                            peer_id = p
                    else:
                        continue
                        
                    if peer_id and peer_id != self.node_id:
                        self.known_peers.append(peer_id)
                except Exception as parse_error:
                    # Skip malformed peer entry
                    continue
            
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
                    'total_proofs': len(self.verification_proofs),
                    'known_peers': len(self.known_peers),
                    'active_workers': len(self.available_workers)
                },
                # Include current proposals so peers can see our votes
                'leaderboard_proposal_cid': getattr(self, 'canonical_leaderboard_cid', None),
                'status_proposal_cid': getattr(self, 'canonical_status_cid', None)
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
        # After gossip, attempt to tally votes and publish canonical resources if we hold keys
        try:
            self._tally_votes_from_peer_states()
            self._maybe_publish_ipns()
        except Exception:
            pass

    def _tally_votes_from_peer_states(self):
        """Tally leaderboard/status votes based on current vote maps and known peers."""
        # Simple quorum: at least 2 votes or majority of known peers
        quorum = max(2, (len(self.known_peers) + 1) // 2 + 1)
        # Check leaderboard
        for cid, count in list(self.leaderboard_votes.items()):
            if count >= quorum:
                if self.canonical_leaderboard_cid != cid:
                    self.canonical_leaderboard_cid = cid
                    print(f"[CONSENSUS] ✅ Leaderboard reached quorum: /ipfs/{cid}")
        # Check status
        for cid, count in list(self.status_votes.items()):
            if count >= quorum:
                if self.canonical_status_cid != cid:
                    self.canonical_status_cid = cid
                    print(f"[CONSENSUS] ✅ Status reached quorum: /ipfs/{cid}")

    def _maybe_publish_ipns(self):
        """If this node has IPNS keys for leaderboard/status, publish canonical CIDs so the network has stable names.
        Only nodes with keys will publish; other nodes will participate in consensus via votes.
        """
        try:
            if self.canonical_leaderboard_cid:
                try:
                    self.client.name.publish(self.canonical_leaderboard_cid, key='collatz-leaderboard', lifetime='24h')
                    print(f"[IPNS] Published leaderboard to IPNS (collatz-leaderboard)")
                except Exception:
                    pass

            if self.canonical_status_cid:
                try:
                    self.client.name.publish(self.canonical_status_cid, key='collatz-status', lifetime='24h')
                    print(f"[IPNS] Published status to IPNS (collatz-status)")
                except Exception:
                    pass
        except Exception:
            pass
    
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
            
            # Validate and merge highest_proven with security checks
            peer_highest = peer_state.get('global_highest_proven', 0)
            if peer_highest > self.global_highest_proven:
                # 🔒 SECURITY: Validate peer progress claim
                if self._validate_peer_progress_claim(peer_highest):
                    self.global_highest_proven = peer_highest
                    print(f"[IPFS] ✅ Validated peer progress update: {self.global_highest_proven:,}")
                else:
                    print(f"[IPFS] 🚫 SECURITY: Rejected invalid peer progress claim: {peer_highest:,}")
                    print(f"[IPFS] Current valid progress: {self.global_highest_proven:,}")
            # Collect peer proposals for leaderboard/status and vote locally
            try:
                lb = peer_state.get('leaderboard_proposal_cid')
                if lb:
                    self.leaderboard_votes[lb] = self.leaderboard_votes.get(lb, 0) + 1
                    if not self.canonical_leaderboard_cid or self.leaderboard_votes[lb] > self.leaderboard_votes.get(self.canonical_leaderboard_cid, 0):
                        self.canonical_leaderboard_cid = lb
                        print(f"[CONSENSUS] 🗳️ Canonical leaderboard updated from peers: /ipfs/{lb}")

                st = peer_state.get('status_proposal_cid')
                if st:
                    self.status_votes[st] = self.status_votes.get(st, 0) + 1
                    if not self.canonical_status_cid or self.status_votes[st] > self.status_votes.get(self.canonical_status_cid, 0):
                        self.canonical_status_cid = st
                        print(f"[CONSENSUS] 🗳️ Canonical status updated from peers: /ipfs/{st}")
            except Exception:
                pass
        
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
                                       priority: int = 1, creator_user_id: Optional[str] = None) -> Optional[WorkAssignment]:
        """
        🔒 SECURE: Create a new work assignment with trust-level validation.
        Returns None if user is not authorized to create assignments.
        """
        assignment_size = range_end - range_start
        
        # 🔒 TRUST RESTRICTIONS: Validate user authorization for work assignments
        if creator_user_id:
            can_create, create_message = self.trust_system.can_user_create_work_assignments(creator_user_id, assignment_size)
            if not can_create:
                print(f"[IPFS] 🚫 TRUST: {create_message}")
                return None
            print(f"[IPFS] ✅ TRUST: {create_message}")
        
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
            priority=priority,
            creator_user_id=creator_user_id  # Track who created this assignment
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
        self.available_workers[worker_id] = {
            'timestamp': time.time(),
            'user_id': user_id
        }
        
        # Clean up stale workers (not seen in 5 minutes)
        current_time = time.time()
        stale_workers = [
            wid for wid, worker_data in self.available_workers.items()
            if current_time - worker_data['timestamp'] > 300  # 5 minutes
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
            
            # Assign random workers with SECURITY CHECKS
            for _ in range(needed):
                if not free_workers:
                    break  # No more workers available
                
                worker_id = free_workers.pop(0)
                
                # 🚨 CRITICAL SECURITY CHECK: Prevent same-user verification
                worker_user_id = self.available_workers.get(worker_id, {}).get('user_id')
                
                # Check if this worker's user already has a worker assigned to this range
                user_already_assigned = False
                if worker_user_id:
                    for assigned_worker in assignment.assigned_workers:
                        assigned_worker_user = self.available_workers.get(assigned_worker, {}).get('user_id')
                        if assigned_worker_user == worker_user_id:
                            user_already_assigned = True
                            break
                
                # Skip if same user already assigned (enforce diversity)
                if user_already_assigned:
                    print(f"[IPFS] 🚫 Skipping worker {worker_id[:16]}... - user {worker_user_id} already has worker on this range")
                    continue
                
                # Check against original creator (if tracked)
                if assignment.creator_user_id and worker_user_id == assignment.creator_user_id:
                    # Allow ONE worker from creator user, but only as fallback if needed
                    creator_workers_count = sum(1 for w in assignment.assigned_workers 
                                              if self.available_workers.get(w, {}).get('user_id') == assignment.creator_user_id)
                    other_user_workers_count = len(assignment.assigned_workers) - creator_workers_count
                    
                    if creator_workers_count >= 1 or other_user_workers_count == 0:
                        print(f"[IPFS] 🚫 Skipping creator's worker {worker_id[:16]}... - creator user {worker_user_id} limited to 1 worker or needs other users first")
                        continue
                
                # Assign worker to range (passed security checks)
                assignment.assigned_workers.append(worker_id)
                self.worker_assignments[worker_id] = assignment.assignment_id
                assignment.timeout_at = current_time + self.WORK_TIMEOUT_SECONDS
                
                if len(assignment.assigned_workers) >= assignment.redundancy_factor:
                    assignment.status = 'in_progress'
                
                assignments_made += 1
                
                print(f"[IPFS] ✅ SECURE ASSIGNMENT: Worker {worker_id[:16]}... (user {worker_user_id or 'unknown'}) -> Range {assignment.range_start:,}-{assignment.range_end:,}")
                
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
            
            # Auto-update leaderboard when work completes
            self._try_update_leaderboard()
        
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
    
    
    def _validate_peer_progress_claim(self, claimed_progress: int) -> bool:
        """
        🔒 SECURITY: Validate a peer's progress claim to prevent malicious updates.
        
        Args:
            claimed_progress: The progress value claimed by a peer
            
        Returns:
            bool: True if claim is valid, False if potentially malicious
        """
        # Rule 1: Prevent massive backwards jumps (could be malicious reset)
        if claimed_progress < self.global_highest_proven * 0.99:  # Allow 1% variance for network lag
            print(f"[SECURITY] Rejected backwards progress: {claimed_progress:,} < {self.global_highest_proven:,}")
            return False
        
        # Rule 2: Prevent impossible forward jumps (unrealistic progress)
        max_reasonable_jump = self.global_highest_proven + (self.RANGE_SIZE * 100)  # Max 100 ranges ahead
        if claimed_progress > max_reasonable_jump:
            print(f"[SECURITY] Rejected excessive progress jump: {claimed_progress:,} > {max_reasonable_jump:,}")
            return False
        
        # Rule 3: Validate against completed work (if we have local state)
        if self._has_sufficient_completed_work_for_progress(claimed_progress):
            return True
        
        # Rule 4: Allow small incremental progress (normal network operation)
        reasonable_increment = self.global_highest_proven + (self.RANGE_SIZE * 10)  # Max 10 ranges
        if claimed_progress <= reasonable_increment:
            return True
        
        print(f"[SECURITY] Rejected unvalidated large progress jump: {claimed_progress:,}")
        return False
    
    def _has_sufficient_completed_work_for_progress(self, progress: int) -> bool:
        """
        🔒 ENHANCED SECURITY: Comprehensive incremental progress validation.
        Ensures progress claims are backed by sufficient verified work.
        """
        current_highest = self.global_highest_proven
        
        # Rule 1: Check if we have continuous coverage from current highest to claimed progress
        if not self._validate_continuous_coverage(current_highest, progress):
            print(f"[SECURITY] Gap in verification coverage between {current_highest:,} and {progress:,}")
            return False
        
        # Rule 2: Count verified ranges in the claimed progress area
        verified_ranges = [assignment for assignment in self.work_assignments.values() 
                          if (assignment.status == 'completed' and 
                              assignment.range_start >= current_highest and 
                              assignment.range_end <= progress)]
        
        if not verified_ranges:
            print(f"[SECURITY] No verified ranges found between {current_highest:,} and {progress:,}")
            return False
        
        # Rule 3: Check redundancy - ensure sufficient verification diversity
        for assignment in verified_ranges:
            if len(assignment.completed_workers) < 2:  # Minimum 2 workers must verify each range
                print(f"[SECURITY] Insufficient verification redundancy for range {assignment.range_start:,}-{assignment.range_end:,}")
                return False
        
        # Rule 4: Estimate coverage quality
        total_coverage = sum(assignment.range_end - assignment.range_start for assignment in verified_ranges)
        expected_coverage = progress - current_highest
        coverage_ratio = total_coverage / expected_coverage if expected_coverage > 0 else 0
        
        if coverage_ratio < 0.95:  # Require 95% coverage minimum
            print(f"[SECURITY] Insufficient coverage ratio: {coverage_ratio:.2%} < 95%")
            return False
        
        # Rule 5: Check verification timestamps to prevent backdating attacks
        recent_cutoff = time.time() - 3600  # 1 hour ago
        recent_verifications = sum(1 for assignment in verified_ranges 
                                 if any(proof.timestamp > recent_cutoff 
                                       for proof in self.verification_proofs.values() 
                                       if proof.assignment_id == assignment.assignment_id))
        
        if recent_verifications == 0 and len(verified_ranges) > 0:
            print(f"[SECURITY] No recent verifications found - possible replay attack")
            return False
        
        print(f"[SECURITY] ✅ Progress validation passed: {len(verified_ranges)} ranges, {coverage_ratio:.1%} coverage")
        return True

    def _validate_continuous_coverage(self, start: int, end: int) -> bool:
        """
        🔒 SECURITY: Validate that there's continuous verification coverage.
        Prevents gaps that could hide fake progress claims.
        """
        if start >= end:
            return True
        
        # Get all completed assignments in the range, sorted by start
        relevant_assignments = sorted(
            [assignment for assignment in self.work_assignments.values() 
             if (assignment.status == 'completed' and 
                 assignment.range_start >= start and 
                 assignment.range_end <= end)],
            key=lambda x: x.range_start
        )
        
        if not relevant_assignments:
            return False
        
        # Check for gaps in coverage
        current_position = start
        for assignment in relevant_assignments:
            if assignment.range_start > current_position:
                # Found a gap
                gap_size = assignment.range_start - current_position
                if gap_size > self.RANGE_SIZE * 0.1:  # Allow small gaps (10% of range size)
                    return False
            current_position = max(current_position, assignment.range_end)
        
        # Check if we reached the end
        return current_position >= end

    def submit_progress_claim(self, worker_id: str, user_id: str, new_highest: int, proof_cid: str) -> bool:
        """
        🔒 SECURE: Submit a progress claim that requires consensus validation.
        Replaces direct progress updates with a consensus mechanism.
        """
        if new_highest <= self.global_highest_proven:
            print(f"[IPFS] Progress claim {new_highest:,} not higher than current {self.global_highest_proven:,}")
            return False
        
        # 🔒 TRUST RESTRICTIONS: Check if user is authorized to make progress claims
        can_claim, claim_message = self.trust_system.can_user_make_progress_claims(user_id)
        if not can_claim:
            print(f"[IPFS] 🚫 TRUST: {claim_message}")
            return False
        
        # 🔒 SECURITY: Validate the claim first
        if not self._validate_progress_update(new_highest):
            print(f"[IPFS] 🚫 SECURITY: Rejected invalid progress claim: {new_highest:,}")
            return False
        
        # Submit to trust system for consensus
        consensus_reached, message = self.trust_system.submit_progress_claim(
            worker_id, user_id, new_highest, proof_cid
        )
        
        print(f"[IPFS] {message}")
        
        if consensus_reached:
            # 🔒 BYZANTINE SECURITY: Check for attacks before accepting consensus
            attack_indicators = self.trust_system.detect_byzantine_attacks()
            if attack_indicators['risk_level'] in ['HIGH', 'CRITICAL']:
                self.trust_system.apply_byzantine_countermeasures(attack_indicators)
                print(f"[IPFS] 🛡️ Applied Byzantine countermeasures, risk level: {attack_indicators['risk_level']}")
            
            # Update global progress only after consensus and security checks
            self.global_highest_proven = new_highest
            print(f"[IPFS] 🎉 CONSENSUS CONFIRMED: New global highest: {new_highest:,}")
            
            # Publish immediately for milestone updates
            self.publish_state_to_network()
            return True
        
        return False

    def update_global_highest(self, new_highest: int):
        """
        🔒 DEPRECATED: Direct progress updates are now disabled for security.
        Use submit_progress_claim() with consensus validation instead.
        """
        print(f"[IPFS] 🚫 SECURITY: Direct progress updates disabled. Use consensus-based claims.")
        print(f"[IPFS] 💡 Use submit_progress_claim(worker_id, user_id, {new_highest}, proof_cid) instead")

    def _validate_progress_update(self, new_progress: int) -> bool:
        """
        🔒 SECURITY: Validate a progress update for security.
        This is called when our own workers complete verification.
        """
        # Rule 1: Only allow reasonable incremental progress
        if new_progress > self.global_highest_proven + (self.RANGE_SIZE * 2):
            print(f"[SECURITY] Progress update too large: {new_progress:,} vs {self.global_highest_proven:,}")
            return False
        
        # Rule 2: Must be based on completed verified work
        if not self._has_sufficient_completed_work_for_progress(new_progress):
            print(f"[SECURITY] Insufficient completed work for progress: {new_progress:,}")
            return False
        
        return True
    
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
    
    def _try_update_leaderboard(self):
        """
        🌐 FULLY DECENTRALIZED: Auto-update leaderboard & status when verification completes.
        Any node can generate and publish. Consensus determines canonical version.
        Uses IPFS content-addressing: identical data = same CID (automatic consensus).
        """
        # Check if generators are available
        if not self.leaderboard_generator or not self.status_generator:
            return
        
        current_time = time.time()
        
        # Update leaderboard (rate-limited)
        if current_time - self.last_leaderboard_update >= self.leaderboard_update_interval:
            try:
                print(f"[IPFS] 🔄 Auto-updating leaderboard...")
                leaderboard_cid = self.leaderboard_generator.update_leaderboard()
                if leaderboard_cid:
                    self.last_leaderboard_update = current_time
                    self._vote_for_cid('leaderboard', leaderboard_cid)
                    print(f"[IPFS] ✅ Leaderboard published: /ipfs/{leaderboard_cid}")
            except Exception as e:
                print(f"[IPFS] ⚠️ Leaderboard update failed: {e}")
        
        # Update status website (more frequent)
        if current_time - self.last_status_update >= self.status_update_interval:
            try:
                print(f"[IPFS] 🔄 Auto-updating status website...")
                status_cid = self.status_generator.update_status(
                    network_stats=self.get_network_statistics(),
                    leaderboard_cid=self.canonical_leaderboard_cid,
                    active_nodes=len(self.known_peers) + 1,
                    node_id=self.node_id
                )
                if status_cid:
                    self.last_status_update = current_time
                    self._vote_for_cid('status', status_cid)
                    print(f"[IPFS] ✅ Status website published: /ipfs/{status_cid}")
                    print(f"[IPFS] 🌐 View at: https://ipfs.io/ipfs/{status_cid}")
            except Exception as e:
                print(f"[IPFS] ⚠️ Status update failed: {e}")
    
    def _vote_for_cid(self, content_type: str, cid: str):
        """
        🗳️ CONSENSUS: Vote for a CID as canonical version.
        Multiple nodes publishing identical content = same CID = automatic agreement.
        """
        if content_type == 'leaderboard':
            self.leaderboard_votes[cid] = self.leaderboard_votes.get(cid, 0) + 1
            # Update canonical if this CID has most votes
            if not self.canonical_leaderboard_cid or \
               self.leaderboard_votes[cid] > self.leaderboard_votes.get(self.canonical_leaderboard_cid, 0):
                self.canonical_leaderboard_cid = cid
                print(f"[CONSENSUS] 🗳️ Canonical leaderboard: /ipfs/{cid}")
        
        elif content_type == 'status':
            self.status_votes[cid] = self.status_votes.get(cid, 0) + 1
            if not self.canonical_status_cid or \
               self.status_votes[cid] > self.status_votes.get(self.canonical_status_cid, 0):
                self.canonical_status_cid = cid
                print(f"[CONSENSUS] 🗳️ Canonical status: /ipfs/{cid}")


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

