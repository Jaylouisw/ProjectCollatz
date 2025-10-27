"""
DISTRIBUTED COLLATZ - TRUST & REPUTATION SYSTEM
================================================
Copyright (c) 2025 Jay Wenden (CollatzEngine)
Licensed under CC BY-NC-SA 4.0

Manages worker reputation, trust levels, and verification consensus.
Prevents Byzantine attacks and ensures result integrity through:
- Multi-worker verification (3+ workers per range)
- Trust scoring based on historical accuracy
- Reputation decay for inactive workers
- Consensus requirements before accepting results
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

class TrustLevel(Enum):
    """Trust levels for workers based on verification history."""
    UNTRUSTED = 0      # New worker, no history (requires 5 confirmations)
    VERIFIED = 1       # 10+ correct verifications (requires 3 confirmations)
    TRUSTED = 2        # 100+ correct verifications (requires 2 confirmations)
    ELITE = 3          # 1000+ correct, 0 errors (requires 1 confirmation)
    BANNED = -1        # Caught submitting false results (permanent)

@dataclass
class WorkerStats:
    """Statistics for a single worker."""
    worker_id: str
    total_verifications: int = 0
    correct_verifications: int = 0
    incorrect_verifications: int = 0
    total_numbers_checked: int = 0
    total_compute_time: float = 0.0  # seconds
    trust_level: TrustLevel = TrustLevel.UNTRUSTED
    reputation_score: float = 0.0
    first_seen: float = None
    last_active: float = None
    consecutive_correct: int = 0
    consecutive_incorrect: int = 0
    
    def __post_init__(self):
        if self.first_seen is None:
            self.first_seen = time.time()
        if self.last_active is None:
            self.last_active = time.time()

@dataclass
class VerificationResult:
    """Result from a worker verification of a range."""
    worker_id: str
    range_start: int
    range_end: int
    all_converged: bool
    numbers_checked: int
    compute_time: float
    timestamp: float
    signature: str  # Cryptographic signature of result
    proof_cid: str  # IPFS CID of detailed proof

@dataclass
class ConsensusState:
    """Consensus tracking for a range verification."""
    range_start: int
    range_end: int
    required_confirmations: int
    confirmations: List[VerificationResult]
    consensus_reached: bool = False
    consensus_result: Optional[bool] = None  # True = all converged, False = counterexample
    conflicting_results: List[VerificationResult] = None
    
    def __post_init__(self):
        if self.conflicting_results is None:
            self.conflicting_results = []

class TrustSystem:
    """Manages worker reputation and verification consensus."""
    
    # Trust level thresholds
    VERIFIED_THRESHOLD = 10      # Correct verifications to become VERIFIED
    TRUSTED_THRESHOLD = 100      # Correct verifications to become TRUSTED
    ELITE_THRESHOLD = 1000       # Correct verifications to become ELITE
    
    # Reputation decay
    DECAY_PERIOD_DAYS = 30       # Days before reputation starts decaying
    DECAY_RATE = 0.95            # Multiplier per month of inactivity
    
    # Consensus requirements (confirmations needed per trust level)
    CONSENSUS_REQUIREMENTS = {
        TrustLevel.UNTRUSTED: 5,  # New workers need 5 confirmations
        TrustLevel.VERIFIED: 3,   # Verified workers need 3
        TrustLevel.TRUSTED: 2,    # Trusted workers need 2
        TrustLevel.ELITE: 1,      # Elite workers need 1 (but still spot-checked)
        TrustLevel.BANNED: 999    # Banned workers ignored
    }
    
    # Spot-check probability (even trusted workers get randomly re-verified)
    SPOT_CHECK_PROBABILITY = {
        TrustLevel.VERIFIED: 0.10,  # 10% spot-check
        TrustLevel.TRUSTED: 0.05,   # 5% spot-check
        TrustLevel.ELITE: 0.02      # 2% spot-check
    }
    
    def __init__(self, storage_file: str = "trust_database.json"):
        """Initialize trust system."""
        self.storage_file = storage_file
        self.workers: Dict[str, WorkerStats] = {}
        self.pending_consensus: Dict[Tuple[int, int], ConsensusState] = {}
        self.load_state()
    
    def load_state(self):
        """Load worker stats from persistent storage."""
        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
                for worker_id, stats_dict in data.get('workers', {}).items():
                    # Convert trust_level string back to enum
                    stats_dict['trust_level'] = TrustLevel[stats_dict['trust_level']]
                    self.workers[worker_id] = WorkerStats(**stats_dict)
        except FileNotFoundError:
            print("[TRUST] No existing trust database, starting fresh")
        except Exception as e:
            print(f"[TRUST] Error loading trust database: {e}")
    
    def save_state(self):
        """Save worker stats to persistent storage."""
        try:
            data = {
                'workers': {
                    worker_id: {
                        **asdict(stats),
                        'trust_level': stats.trust_level.name  # Convert enum to string
                    }
                    for worker_id, stats in self.workers.items()
                },
                'last_updated': time.time()
            }
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[TRUST] Error saving trust database: {e}")
    
    def register_worker(self, worker_id: str) -> WorkerStats:
        """Register a new worker or return existing stats."""
        if worker_id not in self.workers:
            self.workers[worker_id] = WorkerStats(worker_id=worker_id)
            print(f"[TRUST] New worker registered: {worker_id[:16]}... (UNTRUSTED)")
            self.save_state()
        return self.workers[worker_id]
    
    def get_worker_stats(self, worker_id: str) -> Optional[WorkerStats]:
        """Get statistics for a worker."""
        return self.workers.get(worker_id)
    
    def calculate_reputation(self, stats: WorkerStats) -> float:
        """Calculate reputation score for a worker (0.0 to 100.0)."""
        if stats.total_verifications == 0:
            return 0.0
        
        # Base score: accuracy percentage
        accuracy = stats.correct_verifications / stats.total_verifications
        base_score = accuracy * 100.0
        
        # Bonus for volume (logarithmic scaling)
        import math
        volume_bonus = min(20.0, math.log10(stats.total_verifications + 1) * 5.0)
        
        # Penalty for recent errors (consecutive incorrect)
        error_penalty = min(30.0, stats.consecutive_incorrect * 10.0)
        
        # Bonus for consistency (consecutive correct)
        consistency_bonus = min(15.0, stats.consecutive_correct * 0.5)
        
        # Apply reputation decay for inactivity
        days_inactive = (time.time() - stats.last_active) / 86400
        if days_inactive > self.DECAY_PERIOD_DAYS:
            months_inactive = (days_inactive - self.DECAY_PERIOD_DAYS) / 30
            decay_multiplier = self.DECAY_RATE ** months_inactive
        else:
            decay_multiplier = 1.0
        
        # Final score
        reputation = (base_score + volume_bonus + consistency_bonus - error_penalty) * decay_multiplier
        return max(0.0, min(100.0, reputation))
    
    def update_trust_level(self, stats: WorkerStats):
        """Update worker's trust level based on performance."""
        # Banned workers stay banned
        if stats.trust_level == TrustLevel.BANNED:
            return
        
        # Check for ban conditions (more than 10% error rate after 20+ verifications)
        if stats.total_verifications >= 20:
            error_rate = stats.incorrect_verifications / stats.total_verifications
            if error_rate > 0.10 or stats.consecutive_incorrect >= 3:
                stats.trust_level = TrustLevel.BANNED
                print(f"[TRUST] ⛔ Worker {stats.worker_id[:16]}... BANNED (error rate: {error_rate:.1%})")
                return
        
        # Upgrade trust level based on correct verifications
        correct = stats.correct_verifications
        
        if correct >= self.ELITE_THRESHOLD and stats.incorrect_verifications == 0:
            if stats.trust_level != TrustLevel.ELITE:
                stats.trust_level = TrustLevel.ELITE
                print(f"[TRUST] ⭐ Worker {stats.worker_id[:16]}... promoted to ELITE")
        elif correct >= self.TRUSTED_THRESHOLD:
            if stats.trust_level != TrustLevel.TRUSTED:
                stats.trust_level = TrustLevel.TRUSTED
                print(f"[TRUST] ✅ Worker {stats.worker_id[:16]}... promoted to TRUSTED")
        elif correct >= self.VERIFIED_THRESHOLD:
            if stats.trust_level != TrustLevel.VERIFIED:
                stats.trust_level = TrustLevel.VERIFIED
                print(f"[TRUST] ✓ Worker {stats.worker_id[:16]}... promoted to VERIFIED")
    
    def submit_verification(self, result: VerificationResult) -> Tuple[bool, str]:
        """
        Submit a verification result from a worker.
        Returns (consensus_reached, message)
        """
        # Register or update worker
        stats = self.register_worker(result.worker_id)
        stats.last_active = result.timestamp
        stats.total_verifications += 1
        stats.total_numbers_checked += result.numbers_checked
        stats.total_compute_time += result.compute_time
        
        # Get or create consensus state for this range
        range_key = (result.range_start, result.range_end)
        if range_key not in self.pending_consensus:
            # Determine required confirmations based on submitter's trust level
            required = self.CONSENSUS_REQUIREMENTS[stats.trust_level]
            self.pending_consensus[range_key] = ConsensusState(
                range_start=result.range_start,
                range_end=result.range_end,
                required_confirmations=required,
                confirmations=[]
            )
        
        consensus = self.pending_consensus[range_key]
        
        # Check if this worker already submitted for this range
        if any(c.worker_id == result.worker_id for c in consensus.confirmations):
            return False, "Worker already submitted verification for this range"
        
        # Add to confirmations
        consensus.confirmations.append(result)
        
        # Check for consensus
        if len(consensus.confirmations) >= consensus.required_confirmations:
            # All confirmations must agree
            all_results = [c.all_converged for c in consensus.confirmations]
            
            if len(set(all_results)) == 1:
                # Consensus reached!
                consensus.consensus_reached = True
                consensus.consensus_result = all_results[0]
                
                # Update all participating workers as CORRECT
                for confirmation in consensus.confirmations:
                    worker = self.workers[confirmation.worker_id]
                    worker.correct_verifications += 1
                    worker.consecutive_correct += 1
                    worker.consecutive_incorrect = 0
                    worker.reputation_score = self.calculate_reputation(worker)
                    self.update_trust_level(worker)
                
                self.save_state()
                
                result_str = "CONVERGED" if consensus.consensus_result else "⚠️ COUNTEREXAMPLE FOUND"
                return True, f"✅ Consensus reached: {result_str} (confirmed by {len(consensus.confirmations)} workers)"
            else:
                # CONFLICT - workers disagree!
                consensus.conflicting_results = consensus.confirmations.copy()
                
                # Mark all participants as suspicious (need investigation)
                for confirmation in consensus.confirmations:
                    worker = self.workers[confirmation.worker_id]
                    print(f"[TRUST] ⚠️ CONFLICT detected in range {result.range_start:,} - {result.range_end:,}")
                    print(f"[TRUST] Worker {worker.worker_id[:16]}... reported: {confirmation.all_converged}")
                
                # Require additional independent verification
                consensus.required_confirmations += 3
                
                return False, f"⚠️ CONFLICT: Workers disagree! Requesting {consensus.required_confirmations - len(consensus.confirmations)} more verifications"
        else:
            remaining = consensus.required_confirmations - len(consensus.confirmations)
            return False, f"Verification submitted. Waiting for {remaining} more confirmation(s)"
    
    def resolve_conflict(self, range_start: int, range_end: int, correct_result: bool, 
                        correct_workers: List[str], incorrect_workers: List[str]):
        """
        Manually resolve a conflict after independent verification.
        Updates reputation of correct and incorrect workers.
        """
        # Reward correct workers
        for worker_id in correct_workers:
            if worker_id in self.workers:
                stats = self.workers[worker_id]
                stats.correct_verifications += 1
                stats.consecutive_correct += 1
                stats.consecutive_incorrect = 0
                stats.reputation_score = self.calculate_reputation(stats)
                self.update_trust_level(stats)
                print(f"[TRUST] ✅ Worker {worker_id[:16]}... verified correct in conflict")
        
        # Penalize incorrect workers
        for worker_id in incorrect_workers:
            if worker_id in self.workers:
                stats = self.workers[worker_id]
                stats.incorrect_verifications += 1
                stats.consecutive_incorrect += 1
                stats.consecutive_correct = 0
                stats.reputation_score = self.calculate_reputation(stats)
                self.update_trust_level(stats)
                print(f"[TRUST] ❌ Worker {worker_id[:16]}... submitted incorrect result")
        
        # Remove from pending consensus
        range_key = (range_start, range_end)
        if range_key in self.pending_consensus:
            del self.pending_consensus[range_key]
        
        self.save_state()
    
    def get_leaderboard(self, top_n: int = 10) -> List[WorkerStats]:
        """Get top workers by reputation."""
        sorted_workers = sorted(
            self.workers.values(),
            key=lambda w: w.reputation_score,
            reverse=True
        )
        return sorted_workers[:top_n]
    
    def get_statistics(self) -> Dict:
        """Get overall network statistics."""
        if not self.workers:
            return {
                'total_workers': 0,
                'active_workers': 0,
                'total_verifications': 0,
                'total_numbers_checked': 0
            }
        
        active_cutoff = time.time() - 86400  # Active in last 24 hours
        active_workers = sum(1 for w in self.workers.values() if w.last_active > active_cutoff)
        
        return {
            'total_workers': len(self.workers),
            'active_workers': active_workers,
            'total_verifications': sum(w.total_verifications for w in self.workers.values()),
            'total_numbers_checked': sum(w.total_numbers_checked for w in self.workers.values()),
            'total_compute_time': sum(w.total_compute_time for w in self.workers.values()),
            'trust_levels': {
                'ELITE': sum(1 for w in self.workers.values() if w.trust_level == TrustLevel.ELITE),
                'TRUSTED': sum(1 for w in self.workers.values() if w.trust_level == TrustLevel.TRUSTED),
                'VERIFIED': sum(1 for w in self.workers.values() if w.trust_level == TrustLevel.VERIFIED),
                'UNTRUSTED': sum(1 for w in self.workers.values() if w.trust_level == TrustLevel.UNTRUSTED),
                'BANNED': sum(1 for w in self.workers.values() if w.trust_level == TrustLevel.BANNED)
            }
        }
    
    def needs_spot_check(self, worker_id: str) -> bool:
        """Determine if a trusted worker's result needs spot-checking."""
        import random
        
        stats = self.get_worker_stats(worker_id)
        if not stats or stats.trust_level == TrustLevel.UNTRUSTED:
            return True  # Always verify untrusted workers
        
        if stats.trust_level in self.SPOT_CHECK_PROBABILITY:
            probability = self.SPOT_CHECK_PROBABILITY[stats.trust_level]
            return random.random() < probability
        
        return False


# Example usage
if __name__ == "__main__":
    trust = TrustSystem()
    
    # Simulate worker verifications
    result1 = VerificationResult(
        worker_id="QmWorker1",
        range_start=1000000,
        range_end=1001000,
        all_converged=True,
        numbers_checked=500,
        compute_time=10.5,
        timestamp=time.time(),
        signature="sig1",
        proof_cid="Qm123"
    )
    
    consensus, msg = trust.submit_verification(result1)
    print(msg)
    
    # Show statistics
    stats = trust.get_statistics()
    print(f"\nNetwork Stats: {stats}")
    
    # Show leaderboard
    print("\nTop Workers:")
    for i, worker in enumerate(trust.get_leaderboard(5), 1):
        print(f"{i}. {worker.worker_id[:16]}... - Trust: {worker.trust_level.name}, "
              f"Reputation: {worker.reputation_score:.1f}, Correct: {worker.correct_verifications}")
