"""
COUNTEREXAMPLE DETECTION AND NETWORK COORDINATION
==================================================
Copyright (c) 2025 Jay Wenden (CollatzEngine)

Handles the historic moment when a Collatz counterexample is found.
Coordinates network-wide celebration, credits discoverers, manages voting on continuation.

This module is called when:
1. A worker reports all_converged=False
2. Multiple workers (3+) verify the counterexample independently
3. Network enters COUNTEREXAMPLE_FOUND state
4. All nodes are notified to stop and celebrate
5. Community votes whether to continue or shutdown
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

@dataclass
class CounterexampleData:
    """Data about a discovered counterexample."""
    counterexample_number: int
    discovered_by_worker: str
    discovered_by_user: str
    discovered_at: str  # ISO timestamp
    first_verifiers: List[Tuple[str, str]]  # [(worker_id, user_id), ...]
    verification_count: int
    range_start: int
    range_end: int
    assignment_id: str
    ipfs_proof_cid: str  # Permanent record on IPFS
    consensus_reached_at: str  # ISO timestamp when 3+ confirmed


class CounterexampleCoordinator:
    """
    Manages counterexample detection and network celebration.
    
    Critical workflow:
    1. Worker finds potential counterexample (all_converged=False)
    2. Broadcast to all peers: URGENT_VERIFICATION_NEEDED
    3. Random workers (3+) assigned to verify ASAP
    4. If 3+ workers confirm: COUNTEREXAMPLE_VERIFIED
    5. Broadcast celebration message to all nodes
    6. Network enters voting mode
    7. Users vote: continue or shutdown
    8. First to >50% of ACTIVE nodes wins
    """
    
    def __init__(self, ipfs_coordinator):
        """Initialize counterexample coordinator."""
        self.coordinator = ipfs_coordinator
        self.counterexample_found = False
        self.counterexample_data: Optional[CounterexampleData] = None
        self.network_genesis_time: Optional[str] = None
        
        # Voting state
        self.voting_active = False
        self.votes_continue: Dict[str, bool] = {}  # worker_id -> True (continue) or False (shutdown)
        self.voting_deadline: Optional[float] = None
        self.voting_started_at: Optional[str] = None
        
    def check_for_counterexample(self, assignment_id: str, proofs: List[Dict]) -> Optional[CounterexampleData]:
        """
        Check if a counterexample has been found with sufficient verification.
        
        Args:
            assignment_id: The work assignment being checked
            proofs: List of verification proofs for this assignment
            
        Returns:
            CounterexampleData if counterexample verified, None otherwise
        """
        # Filter proofs reporting counterexample (all_converged=False)
        counterexample_proofs = [p for p in proofs if not p.get('all_converged', True)]
        
        if len(counterexample_proofs) < 3:
            return None  # Need 3+ confirmations
        
        # Sort by timestamp to find original discoverer
        counterexample_proofs.sort(key=lambda p: p.get('timestamp', 0))
        
        first_proof = counterexample_proofs[0]
        first_verifiers = [(p.get('worker_id', 'unknown'), p.get('user_id', 'anonymous')) 
                           for p in counterexample_proofs[1:3]]  # First 2 verifiers
        
        # Create counterexample record
        counterexample = CounterexampleData(
            counterexample_number=first_proof.get('range_start', 0),  # Actual number TBD from detailed proof
            discovered_by_worker=first_proof.get('worker_id', 'unknown'),
            discovered_by_user=first_proof.get('user_id', 'anonymous'),
            discovered_at=datetime.fromtimestamp(first_proof.get('timestamp', time.time())).isoformat(),
            first_verifiers=first_verifiers,
            verification_count=len(counterexample_proofs),
            range_start=first_proof.get('range_start', 0),
            range_end=first_proof.get('range_end', 0),
            assignment_id=assignment_id,
            ipfs_proof_cid=first_proof.get('ipfs_cid', ''),
            consensus_reached_at=datetime.now().isoformat()
        )
        
        return counterexample
    
    def broadcast_counterexample_found(self, counterexample: CounterexampleData):
        """
        Broadcast to all nodes that a counterexample has been found.
        This is a HISTORIC MOMENT!
        """
        self.counterexample_found = True
        self.counterexample_data = counterexample
        
        # Create celebration message
        message = {
            "event": "COUNTEREXAMPLE_FOUND",
            "counterexample": asdict(counterexample),
            "message": "🎉 COLLATZ CONJECTURE DISPROVEN! 🎉",
            "timestamp": datetime.now().isoformat(),
            "action_required": "ALL_NODES_STOP_AND_VOTE"
        }
        
        # Upload to IPFS for permanent record
        celebration_cid = self.coordinator.client.add_json(message)
        print(f"\n{'=' * 70}")
        print(f"🎉 COUNTEREXAMPLE FOUND - BROADCAST TO NETWORK 🎉")
        print(f"{'=' * 70}")
        print(f"IPFS Record: /ipfs/{celebration_cid}")
        print(f"{'=' * 70}\n")
        
        # Publish to IPNS so all nodes see it
        try:
            self.coordinator.publish_state_to_network(counterexample_found=True)
        except Exception as e:
            print(f"[WARNING] Could not publish to IPNS: {e}")
        
        return celebration_cid
    
    def display_celebration_message(self, genesis_timestamp: Optional[str] = None):
        """
        Display the historic celebration message.
        Shows project history, credits discoverers, explains significance.
        """
        if not self.counterexample_data:
            return
        
        ce = self.counterexample_data
        
        # Calculate project duration
        if genesis_timestamp:
            try:
                genesis = datetime.fromisoformat(genesis_timestamp)
                now = datetime.now()
                duration = now - genesis
                days = duration.days
                hours, remainder = divmod(duration.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = f"{days} days, {hours} hours, {minutes} minutes"
            except:
                duration_str = "unknown duration"
        else:
            duration_str = "unknown duration"
        
        # Build celebration message
        print("\n\n")
        print("=" * 70)
        print("🎊 🎉 HISTORIC MATHEMATICAL DISCOVERY 🎉 🎊")
        print("=" * 70)
        print()
        print("    ██████╗ ██████╗ ██╗   ██╗███╗   ██╗████████╗███████╗██████╗ ")
        print("   ██╔════╝██╔═══██╗██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗")
        print("   ██║     ██║   ██║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝")
        print("   ██║     ██║   ██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗")
        print("   ╚██████╗╚██████╔╝╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║")
        print("    ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝")
        print()
        print("   ███████╗ ██████╗ ██╗   ██╗███╗   ██╗██████╗ ██╗")
        print("   ██╔════╝██╔═══██╗██║   ██║████╗  ██║██╔══██╗██║")
        print("   █████╗  ██║   ██║██║   ██║██╔██╗ ██║██║  ██║██║")
        print("   ██╔══╝  ██║   ██║██║   ██║██║╚██╗██║██║  ██║╚═╝")
        print("   ██║     ╚██████╔╝╚██████╔╝██║ ╚████║██████╔╝██╗")
        print("   ╚═╝      ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═════╝ ╚═╝")
        print()
        print("=" * 70)
        print()
        print("  THE COLLATZ CONJECTURE HAS BEEN DISPROVEN!")
        print()
        print(f"  After {duration_str} of distributed computation,")
        print(f"  a counterexample has been discovered and independently verified.")
        print()
        print("  This is a momentous achievement in mathematics.")
        print("  You have ALL contributed to making history.")
        print()
        print("=" * 70)
        print()
        print("📊 DISCOVERY DETAILS:")
        print()
        print(f"   Counterexample Number: {ce.counterexample_number:,}")
        print(f"   Range: {ce.range_start:,} to {ce.range_end:,}")
        print(f"   Discovered: {ce.discovered_at}")
        print(f"   Verified: {ce.consensus_reached_at}")
        print(f"   Independent Verifications: {ce.verification_count}")
        print()
        print("=" * 70)
        print()
        print("🏆 SPECIAL RECOGNITION:")
        print()
        print(f"   DISCOVERER:")
        if ce.discovered_by_user != 'anonymous':
            print(f"      👤 User: {ce.discovered_by_user}")
        print(f"      🔧 Worker: {ce.discovered_by_worker[:20]}...")
        print(f"      ⏰ Time: {ce.discovered_at}")
        print()
        print(f"   FIRST VERIFIERS:")
        for i, (worker, user) in enumerate(ce.first_verifiers, 1):
            if user != 'anonymous':
                print(f"      {i}. 👤 User: {user}")
            print(f"         🔧 Worker: {worker[:20]}...")
        print()
        print("   These individuals have changed mathematical history forever.")
        print()
        print("=" * 70)
        print()
        print("🌍 NETWORK IMPACT:")
        print()
        if genesis_timestamp:
            print(f"   Project Started: {genesis_timestamp}")
        print(f"   Duration: {duration_str}")
        print(f"   Permanent Record: /ipfs/{ce.ipfs_proof_cid}")
        print()
        print("   This discovery belongs to the entire distributed community.")
        print("   Every node that contributed helped make this possible.")
        print()
        print("=" * 70)
        print()
        print("📝 WHAT HAPPENS NEXT:")
        print()
        print("   The network will now vote on whether to:")
        print()
        print("      A) CONTINUE searching for additional counterexamples")
        print("      B) SHUTDOWN the project (mission accomplished)")
        print()
        print("   Vote is decided by >50% of ACTIVE nodes.")
        print("   Voting window: 24 hours")
        print()
        print("=" * 70)
        print()
        input("Press ENTER to participate in the vote...")
        print()
    
    def start_voting(self, voting_duration_hours: int = 24):
        """
        Start the voting process for network continuation.
        
        Args:
            voting_duration_hours: How long to allow voting (default 24 hours)
        """
        self.voting_active = True
        self.voting_started_at = datetime.now().isoformat()
        self.voting_deadline = time.time() + (voting_duration_hours * 3600)
        self.votes_continue = {}
        
        print("=" * 70)
        print("🗳️  VOTING NOW OPEN")
        print("=" * 70)
        print()
        print("QUESTION: Should the Collatz network continue operating?")
        print()
        print("OPTIONS:")
        print("  [Y] YES - Continue searching for additional counterexamples")
        print("  [N] NO  - Shutdown the project (mission accomplished)")
        print()
        deadline_str = datetime.fromtimestamp(self.voting_deadline).strftime("%Y-%m-%d %H:%M:%S")
        print(f"Voting closes: {deadline_str}")
        print()
        print("=" * 70)
        print()
    
    def submit_vote(self, worker_id: str, user_id: Optional[str], vote_continue: bool) -> bool:
        """
        Submit a vote from a worker node.
        
        Args:
            worker_id: The worker submitting the vote
            user_id: The user account (if any)
            vote_continue: True to continue, False to shutdown
            
        Returns:
            True if vote accepted, False if rejected
        """
        if not self.voting_active:
            print("[VOTE] Voting is not currently active")
            return False
        
        if time.time() > self.voting_deadline:
            print("[VOTE] Voting deadline has passed")
            self.voting_active = False
            return False
        
        # Record vote (one vote per worker)
        self.votes_continue[worker_id] = vote_continue
        
        vote_str = "CONTINUE" if vote_continue else "SHUTDOWN"
        print(f"[VOTE] Vote recorded: {vote_str}")
        if user_id:
            print(f"[VOTE] User: {user_id}")
        print(f"[VOTE] Worker: {worker_id[:20]}...")
        
        # Check if decision reached
        return self.check_voting_result()
    
    def check_voting_result(self) -> bool:
        """
        Check if voting has reached a decision (>50% threshold).
        
        Returns:
            True if decision reached, False if voting continues
        """
        if not self.votes_continue:
            return False
        
        total_votes = len(self.votes_continue)
        votes_to_continue = sum(1 for v in self.votes_continue.values() if v)
        votes_to_shutdown = total_votes - votes_to_continue
        
        continue_pct = (votes_to_continue / total_votes) * 100
        shutdown_pct = (votes_to_shutdown / total_votes) * 100
        
        print(f"\n[VOTE] Current tally:")
        print(f"   Continue: {votes_to_continue} ({continue_pct:.1f}%)")
        print(f"   Shutdown: {votes_to_shutdown} ({shutdown_pct:.1f}%)")
        print(f"   Total active nodes: {total_votes}")
        
        # Check for majority (>50%)
        if continue_pct > 50.0:
            print(f"\n[VOTE] ✅ DECISION REACHED: CONTINUE")
            print(f"   The network will continue searching for additional counterexamples.")
            self.voting_active = False
            return True
        elif shutdown_pct > 50.0:
            print(f"\n[VOTE] ✅ DECISION REACHED: SHUTDOWN")
            print(f"   The network will shutdown. Mission accomplished!")
            self.voting_active = False
            return True
        
        return False
    
    def get_voting_stats(self) -> Dict:
        """Get current voting statistics."""
        if not self.votes_continue:
            return {
                "active": self.voting_active,
                "total_votes": 0,
                "votes_continue": 0,
                "votes_shutdown": 0,
                "deadline": self.voting_deadline
            }
        
        total = len(self.votes_continue)
        continue_votes = sum(1 for v in self.votes_continue.values() if v)
        shutdown_votes = total - continue_votes
        
        return {
            "active": self.voting_active,
            "total_votes": total,
            "votes_continue": continue_votes,
            "votes_shutdown": shutdown_votes,
            "continue_percentage": (continue_votes / total * 100) if total > 0 else 0,
            "shutdown_percentage": (shutdown_votes / total * 100) if total > 0 else 0,
            "deadline": self.voting_deadline,
            "decision_reached": continue_votes > total/2 or shutdown_votes > total/2
        }
