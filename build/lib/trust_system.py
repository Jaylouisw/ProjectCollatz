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
    user_id: Optional[str] = None  # Link to user account
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
    user_id: Optional[str]  # User who owns this worker - CRITICAL for preventing self-verification
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
    
    
    def register_worker(self, worker_id: str, user_id: Optional[str] = None) -> WorkerStats:
        """Register a new worker or return existing stats. Can link to user account."""
        if worker_id not in self.workers:
            self.workers[worker_id] = WorkerStats(worker_id=worker_id, user_id=user_id)
            if user_id:
                print(f"[TRUST] New worker registered: {worker_id[:16]}... (UNTRUSTED) - User: {user_id}")
            else:
                print(f"[TRUST] New worker registered: {worker_id[:16]}... (UNTRUSTED)")
            self.save_state()
        elif user_id and not self.workers[worker_id].user_id:
            # Link existing worker to user account
            self.workers[worker_id].user_id = user_id
            self.save_state()
        return self.workers[worker_id]
    
    def get_workers_by_user(self, user_id: str) -> List[WorkerStats]:
        """Get all workers belonging to a user."""
        return [w for w in self.workers.values() if w.user_id == user_id]
    
    def get_user_aggregate_stats(self, user_id: str) -> Dict:
        """Get aggregated statistics for all of a user's workers."""
        user_workers = self.get_workers_by_user(user_id)
        
        if not user_workers:
            return {
                'total_workers': 0,
                'total_verifications': 0,
                'total_numbers_checked': 0,
                'total_compute_time': 0.0,
                'average_reputation': 0.0
            }
        
        return {
            'total_workers': len(user_workers),
            'total_verifications': sum(w.total_verifications for w in user_workers),
            'correct_verifications': sum(w.correct_verifications for w in user_workers),
            'incorrect_verifications': sum(w.incorrect_verifications for w in user_workers),
            'total_numbers_checked': sum(w.total_numbers_checked for w in user_workers),
            'total_compute_time': sum(w.total_compute_time for w in user_workers),
            'average_reputation': sum(w.reputation_score for w in user_workers) / len(user_workers),
            'best_trust_level': max((w.trust_level for w in user_workers), key=lambda t: t.value)
        }
    
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
        
        CRITICAL SECURITY RULES:
        1. Workers CANNOT verify their own work 
        2. At least ONE verification must be from a different user
        3. Same-user workers can provide ONE verification as fallback only
        """
        # Register or update worker
        stats = self.register_worker(result.worker_id)
        stats.last_active = result.timestamp
        stats.total_verifications += 1
        stats.total_numbers_checked += result.numbers_checked
        stats.total_compute_time += result.compute_time
        
        # Set user_id in worker stats if provided
        if result.user_id and not stats.user_id:
            stats.user_id = result.user_id
        
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
        
        # 🚨 CRITICAL SECURITY CHECK: Prevent self-verification
        # Check if this is the ORIGINAL worker who did the computation
        if len(consensus.confirmations) == 0:
            # This is the first submission - the original worker
            consensus.confirmations.append(result)
            remaining = consensus.required_confirmations - len(consensus.confirmations)
            return False, f"🔒 Original work submitted. Awaiting {remaining} independent verification(s) from OTHER workers"
        
        # 🚨 PREVENT SAME-WORKER VERIFICATION
        if result.worker_id in [c.worker_id for c in consensus.confirmations]:
            return False, "🚫 SECURITY VIOLATION: Worker cannot verify their own work"
        
        # 🚨 CHECK USER-LEVEL VERIFICATION RULES
        original_user = consensus.confirmations[0].user_id
        current_user = result.user_id
        
        # Count verifications by user
        user_verification_count = {}
        for conf in consensus.confirmations:
            user_id = conf.user_id or "unknown"
            user_verification_count[user_id] = user_verification_count.get(user_id, 0) + 1
        
        current_user_count = user_verification_count.get(current_user or "unknown", 0)
        other_user_count = sum(count for user, count in user_verification_count.items() 
                              if user != original_user)
        
        # Rule: At least ONE verification MUST be from a different user
        if current_user == original_user and other_user_count == 0 and len(consensus.confirmations) >= 2:
            return False, f"🚫 SECURITY RULE: At least ONE verification must be from a different user. Current user {current_user or 'unknown'} cannot provide second verification until another user verifies."
        
        # Rule: Same user can only provide ONE verification (as fallback)
        if current_user == original_user and current_user_count >= 1:
            return False, f"🚫 SECURITY RULE: User {current_user or 'unknown'} can only provide ONE verification per range"
        
        # Add to confirmations (passed security checks)
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
        """Determine if a worker needs a spot-check verification."""
        import random
        
        stats = self.get_worker_stats(worker_id)
        if not stats or stats.trust_level == TrustLevel.UNTRUSTED:
            return True  # Always verify untrusted workers
        
        if stats.trust_level in self.SPOT_CHECK_PROBABILITY:
            probability = self.SPOT_CHECK_PROBABILITY[stats.trust_level]
            return random.random() < probability
        
        return False

    # 🔒 CONSENSUS METHODS FOR PROGRESS UPDATES

    def submit_progress_claim(self, worker_id: str, user_id: str, claimed_progress: int, proof_cid: str) -> Tuple[bool, str]:
        """
        🔒 SECURITY: Submit a progress claim that requires consensus validation.
        
        Args:
            worker_id: ID of the worker making the claim
            user_id: ID of the user who owns the worker
            claimed_progress: The progress value being claimed
            proof_cid: IPFS CID containing proof of the claimed progress
            
        Returns:
            Tuple[bool, str]: (consensus_reached, status_message)
        """
        stats = self.get_worker_stats(worker_id)
        if not stats:
            return False, f"Unknown worker {worker_id[:16]}..."
        
        if stats.trust_level == TrustLevel.BANNED:
            return False, f"Banned worker {worker_id[:16]}... cannot submit progress claims"
        
        # Create consensus key for this progress level
        progress_key = f"progress_{claimed_progress}"
        
        if progress_key not in self.pending_consensus:
            self.pending_consensus[progress_key] = {
                'claimed_progress': claimed_progress,
                'required_confirmations': self._get_required_confirmations_for_progress(),
                'confirmations': [],
                'consensus_reached': False,
                'first_claim_time': time.time()
            }
        
        consensus_state = self.pending_consensus[progress_key]
        
        # Check if this worker/user already contributed to this consensus
        for existing_claim in consensus_state['confirmations']:
            if (existing_claim['worker_id'] == worker_id or 
                existing_claim['user_id'] == user_id):
                return False, f"Worker/User already submitted claim for progress {claimed_progress:,}"
        
        # Add this claim to consensus
        consensus_state['confirmations'].append({
            'worker_id': worker_id,
            'user_id': user_id,
            'proof_cid': proof_cid,
            'timestamp': time.time(),
            'trust_level': stats.trust_level.name
        })
        
        confirmations = len(consensus_state['confirmations'])
        required = consensus_state['required_confirmations']
        
        if confirmations >= required:
            consensus_state['consensus_reached'] = True
            return True, f"🎉 CONSENSUS REACHED: Progress {claimed_progress:,} confirmed by {confirmations} workers"
        
        return False, f"Progress claim recorded ({confirmations}/{required} confirmations needed)"

    def _get_required_confirmations_for_progress(self) -> int:
        """
        🔒 BYZANTINE FAULT TOLERANCE: Calculate confirmations needed to resist malicious nodes.
        Uses (3f + 1) formula where f is the maximum number of malicious nodes.
        """
        # Count active workers across all trust levels (excluding banned)
        active_workers = sum(1 for stats in self.workers.values() 
                           if stats.trust_level != TrustLevel.BANNED
                           and (time.time() - stats.last_active) < 86400)  # Active in last 24h
        
        if active_workers < 3:
            return active_workers  # Need all workers if less than 3
        
        # Byzantine fault tolerance: can handle up to f malicious nodes with 3f + 1 total nodes
        # We calculate required confirmations to ensure honest majority
        max_malicious = active_workers // 3  # Maximum malicious nodes we can tolerate
        
        # Required confirmations for Byzantine consensus
        # Need at least 2f + 1 confirmations where f is max malicious nodes
        required_confirmations = 2 * max_malicious + 1
        
        # Minimum safety: always require at least 3 confirmations
        required_confirmations = max(3, required_confirmations)
        
        # Maximum practical: don't require more than 2/3 of active workers
        max_practical = (active_workers * 2) // 3
        required_confirmations = min(required_confirmations, max_practical)
        
        print(f"[TRUST] 🛡️ Byzantine tolerance: {active_workers} active workers, "
              f"can handle {max_malicious} malicious, requiring {required_confirmations} confirmations")
        
        return required_confirmations

    def get_consensus_status(self, progress_level: int) -> Optional[Dict]:
        """Get current consensus status for a progress level."""
        progress_key = f"progress_{progress_level}"
        return self.pending_consensus.get(progress_key)

    def clean_old_consensus(self, max_age_hours: int = 24):
        """Clean up old consensus attempts that never reached agreement."""
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        expired_keys = []
        for key, consensus_state in self.pending_consensus.items():
            if consensus_state['first_claim_time'] < cutoff_time and not consensus_state['consensus_reached']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.pending_consensus[key]
            print(f"[TRUST] 🗑️ Cleaned expired consensus attempt: {key}")

    def is_progress_consensus_reached(self, progress_level: int) -> bool:
        """Check if consensus has been reached for a specific progress level."""
        progress_key = f"progress_{progress_level}"
        consensus_state = self.pending_consensus.get(progress_key)
        return consensus_state['consensus_reached'] if consensus_state else False

    def detect_byzantine_attacks(self) -> Dict[str, any]:
        """
        🔒 BYZANTINE DETECTION: Analyze consensus patterns to detect potential attacks.
        Returns information about suspicious activities that could indicate malicious nodes.
        """
        current_time = time.time()
        attack_indicators = {
            'suspicious_workers': [],
            'coordinated_attacks': [],
            'timing_anomalies': [],
            'trust_level_violations': [],
            'risk_level': 'LOW'  # LOW, MEDIUM, HIGH, CRITICAL
        }
        
        # Analyze worker behavior patterns
        for worker_id, stats in self.workers.items():
            suspicion_score = 0
            reasons = []
            
            # Check for unusual error patterns
            if stats.total_verifications > 10:
                error_rate = stats.incorrect_verifications / stats.total_verifications
                if error_rate > 0.15:  # More than 15% error rate
                    suspicion_score += 3
                    reasons.append(f"High error rate: {error_rate:.1%}")
            
            # Check for timing anomalies (submissions too fast/slow)
            if stats.total_compute_time > 0 and stats.total_numbers_checked > 0:
                avg_speed = stats.total_numbers_checked / stats.total_compute_time
                if avg_speed > 1000000:  # Unrealistically fast (>1M numbers/second)
                    suspicion_score += 4
                    reasons.append(f"Unrealistic computation speed: {avg_speed:.0f} nums/sec")
                elif avg_speed < 100:  # Unrealistically slow (<100 numbers/second)
                    suspicion_score += 2
                    reasons.append(f"Unusually slow computation: {avg_speed:.0f} nums/sec")
            
            # Check for inconsistent trust level behavior
            if stats.trust_level == TrustLevel.ELITE and stats.consecutive_incorrect > 0:
                suspicion_score += 3
                reasons.append("Elite worker with recent errors")
            
            # Check for rapid trust level changes (possible Sybil attack)
            if (stats.trust_level in [TrustLevel.TRUSTED, TrustLevel.ELITE] and 
                stats.total_verifications < 50):
                suspicion_score += 2
                reasons.append("High trust level with low verification count")
            
            if suspicion_score >= 3:
                attack_indicators['suspicious_workers'].append({
                    'worker_id': worker_id,
                    'user_id': stats.user_id,
                    'suspicion_score': suspicion_score,
                    'reasons': reasons,
                    'trust_level': stats.trust_level.name
                })
        
        # Analyze consensus attempts for coordinated attacks
        consensus_attempts = list(self.pending_consensus.values())
        
        # Look for multiple consensus attempts from same users (Sybil attack)
        user_consensus_counts = {}
        for consensus in consensus_attempts:
            for confirmation in consensus['confirmations']:
                user_id = confirmation['user_id']
                if user_id:
                    user_consensus_counts[user_id] = user_consensus_counts.get(user_id, 0) + 1
        
        for user_id, count in user_consensus_counts.items():
            if count > 3:  # Same user contributing to many consensus attempts
                attack_indicators['coordinated_attacks'].append({
                    'user_id': user_id,
                    'consensus_contributions': count,
                    'type': 'Potential Sybil attack'
                })
        
        # Calculate overall risk level
        total_suspicious = len(attack_indicators['suspicious_workers'])
        total_coordinated = len(attack_indicators['coordinated_attacks'])
        
        if total_suspicious >= 3 or total_coordinated >= 2:
            attack_indicators['risk_level'] = 'CRITICAL'
        elif total_suspicious >= 2 or total_coordinated >= 1:
            attack_indicators['risk_level'] = 'HIGH'
        elif total_suspicious >= 1:
            attack_indicators['risk_level'] = 'MEDIUM'
        
        if attack_indicators['risk_level'] != 'LOW':
            print(f"[TRUST] 🚨 BYZANTINE THREAT DETECTED: Risk level {attack_indicators['risk_level']}")
            print(f"[TRUST] Suspicious workers: {total_suspicious}, Coordinated attacks: {total_coordinated}")
        
        return attack_indicators

    def apply_byzantine_countermeasures(self, attack_indicators: Dict[str, any]):
        """
        🔒 BYZANTINE COUNTERMEASURES: Apply security measures based on detected threats.
        """
        if attack_indicators['risk_level'] == 'LOW':
            return
        
        print(f"[TRUST] 🛡️ Applying Byzantine countermeasures for {attack_indicators['risk_level']} risk")
        
        # Countermeasure 1: Increase consensus requirements temporarily
        if attack_indicators['risk_level'] in ['HIGH', 'CRITICAL']:
            # This will be picked up by _get_required_confirmations_for_progress()
            print("[TRUST] 🔒 Increased consensus requirements due to Byzantine threat")
        
        # Countermeasure 2: Ban highly suspicious workers
        for suspicious in attack_indicators['suspicious_workers']:
            if suspicious['suspicion_score'] >= 5:  # High suspicion threshold
                worker_id = suspicious['worker_id']
                if worker_id in self.workers:
                    self.workers[worker_id].trust_level = TrustLevel.BANNED
                    print(f"[TRUST] ⛔ BANNED worker {worker_id[:16]}... due to Byzantine behavior")
        
        # Countermeasure 3: Reset trust for coordinated attacks
        for attack in attack_indicators['coordinated_attacks']:
            user_id = attack['user_id']
            if user_id:
                # Find all workers belonging to this user and reduce their trust
                for worker_id, stats in self.workers.items():
                    if stats.user_id == user_id and stats.trust_level != TrustLevel.BANNED:
                        if stats.trust_level in [TrustLevel.TRUSTED, TrustLevel.ELITE]:
                            stats.trust_level = TrustLevel.VERIFIED
                            print(f"[TRUST] ⬇️ Demoted worker {worker_id[:16]}... due to coordinated attack")
        
        # Save changes immediately
        self.save_state()

    # 🔒 TRUST-LEVEL RESTRICTIONS

    def can_user_make_progress_claims(self, user_id: str) -> Tuple[bool, str]:
        """
        🔒 TRUST RESTRICTIONS: Check if a user can make progress claims.
        Only trusted users can make significant state changes.
        """
        if not user_id:
            return False, "Anonymous users cannot make progress claims"
        
        # Find the highest trust level worker for this user
        user_workers = [stats for stats in self.workers.values() if stats.user_id == user_id]
        
        if not user_workers:
            return False, f"No workers found for user {user_id}"
        
        # Check if user has any banned workers (major red flag)
        banned_workers = [stats for stats in user_workers if stats.trust_level == TrustLevel.BANNED]
        if banned_workers:
            return False, f"User {user_id} has banned workers - progress claims denied"
        
        # Get highest trust level across user's workers
        highest_trust = max(user_workers, key=lambda x: x.trust_level.value).trust_level
        
        # Trust level requirements for progress claims
        if highest_trust == TrustLevel.UNTRUSTED:
            return False, f"User {user_id} has only untrusted workers - need VERIFIED or higher"
        elif highest_trust == TrustLevel.VERIFIED:
            # Verified users can make small progress claims
            return True, f"User {user_id} verified - can make limited progress claims"
        elif highest_trust in [TrustLevel.TRUSTED, TrustLevel.ELITE]:
            # Trusted/Elite users can make any progress claims
            return True, f"User {user_id} highly trusted - can make any progress claims"
        
        return False, f"Unknown trust level for user {user_id}"

    def can_user_create_work_assignments(self, user_id: str, assignment_size: int) -> Tuple[bool, str]:
        """
        🔒 TRUST RESTRICTIONS: Check if a user can create work assignments.
        Prevents untrusted users from creating massive work assignments.
        """
        if not user_id:
            return False, "Anonymous users cannot create work assignments"
        
        user_workers = [stats for stats in self.workers.values() if stats.user_id == user_id]
        
        if not user_workers:
            return False, f"No workers found for user {user_id}"
        
        # Check for banned workers
        banned_workers = [stats for stats in user_workers if stats.trust_level == TrustLevel.BANNED]
        if banned_workers:
            return False, f"User {user_id} has banned workers - cannot create assignments"
        
        highest_trust = max(user_workers, key=lambda x: x.trust_level.value).trust_level
        
        # Size limits based on trust level
        size_limits = {
            TrustLevel.UNTRUSTED: 10000,      # 10K numbers max
            TrustLevel.VERIFIED: 100000,      # 100K numbers max
            TrustLevel.TRUSTED: 1000000,      # 1M numbers max
            TrustLevel.ELITE: float('inf')    # No limit
        }
        
        max_size = size_limits.get(highest_trust, 0)
        
        if assignment_size > max_size:
            return False, f"Assignment size {assignment_size:,} exceeds limit {max_size:,} for trust level {highest_trust.name}"
        
        return True, f"User {user_id} can create assignment of size {assignment_size:,}"

    def can_user_modify_global_state(self, user_id: str) -> Tuple[bool, str]:
        """
        🔒 TRUST RESTRICTIONS: Check if a user can modify critical global state.
        Only highly trusted users can make network-wide changes.
        """
        if not user_id:
            return False, "Anonymous users cannot modify global state"
        
        user_workers = [stats for stats in self.workers.values() if stats.user_id == user_id]
        
        if not user_workers:
            return False, f"No workers found for user {user_id}"
        
        # Check for banned workers
        banned_workers = [stats for stats in user_workers if stats.trust_level == TrustLevel.BANNED]
        if banned_workers:
            return False, f"User {user_id} has banned workers - cannot modify global state"
        
        highest_trust = max(user_workers, key=lambda x: x.trust_level.value).trust_level
        
        # Only ELITE users can modify global state
        if highest_trust == TrustLevel.ELITE:
            # Additional verification: must have significant history
            elite_workers = [stats for stats in user_workers if stats.trust_level == TrustLevel.ELITE]
            total_verifications = sum(stats.total_verifications for stats in elite_workers)
            
            if total_verifications >= 1000:  # Must have 1000+ verifications
                return True, f"User {user_id} authorized for global state changes"
            else:
                return False, f"User {user_id} ELITE but insufficient history ({total_verifications} verifications)"
        
        return False, f"User {user_id} trust level {highest_trust.name} insufficient for global state changes"

    def get_trust_restrictions_summary(self, user_id: str) -> Dict[str, any]:
        """Get a summary of what a user can and cannot do based on trust level."""
        if not user_id:
            return {'error': 'No user ID provided'}
        
        user_workers = [stats for stats in self.workers.values() if stats.user_id == user_id]
        
        if not user_workers:
            return {'error': f'No workers found for user {user_id}'}
        
        highest_trust = max(user_workers, key=lambda x: x.trust_level.value).trust_level
        total_verifications = sum(stats.total_verifications for stats in user_workers)
        
        can_progress, progress_msg = self.can_user_make_progress_claims(user_id)
        can_assign, assign_msg = self.can_user_create_work_assignments(user_id, 100000)  # Test with 100K
        can_global, global_msg = self.can_user_modify_global_state(user_id)
        
        return {
            'user_id': user_id,
            'highest_trust_level': highest_trust.name,
            'total_verifications': total_verifications,
            'worker_count': len(user_workers),
            'capabilities': {
                'make_progress_claims': can_progress,
                'create_work_assignments': can_assign,
                'modify_global_state': can_global
            },
            'messages': {
                'progress': progress_msg,
                'assignments': assign_msg,
                'global': global_msg
            }
        }


# Example usage
if __name__ == "__main__":
    trust = TrustSystem()
    
    # Simulate worker verifications
    result1 = VerificationResult(
        worker_id="QmWorker1",
        user_id="user_example123",  # CRITICAL: Include user_id for security
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
