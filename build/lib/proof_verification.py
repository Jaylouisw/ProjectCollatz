"""
DISTRIBUTED COLLATZ - PROOF VERIFICATION SYSTEM
================================================
Copyright (c) 2025 Jay Wenden (CollatzEngine)
Licensed under CC BY-NC-SA 4.0

Verifies cryptographic signatures on worker proofs and cross-checks results.
Prevents tampering and ensures Byzantine fault tolerance.

Security features:
- Ed25519 signatures for proof authenticity
- SHA-256 hashing of proof data
- Cross-verification between multiple workers
- Spot-checking of trusted workers
- Automatic conflict detection and resolution
"""

import json
import hashlib
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.exceptions import InvalidSignature
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("[CRYPTO] cryptography not installed. Run: pip install cryptography")

from trust_system import TrustSystem, VerificationResult, TrustLevel


@dataclass
class SignedProof:
    """A cryptographically signed verification proof."""
    # Proof data
    worker_id: str
    range_start: int
    range_end: int
    all_converged: bool
    numbers_checked: int
    max_steps: int
    compute_time: float
    timestamp: float
    ipfs_cid: str  # CID of detailed proof on IPFS
    
    # Cryptographic data
    public_key_pem: str  # Worker's public key (PEM format)
    signature_hex: str   # Signature of proof hash
    proof_hash: str      # SHA-256 hash of proof data
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SignedProof':
        """Create from dictionary."""
        return cls(**data)


class ProofVerificationSystem:
    """Verifies and cross-checks worker proofs."""
    
    def __init__(self, trust_system: TrustSystem):
        """Initialize verification system."""
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography library not available")
        
        self.trust_system = trust_system
        
        # Worker key storage (public keys only)
        self.worker_keys: Dict[str, ed25519.Ed25519PublicKey] = {}
        
        # Pending cross-verifications
        self.pending_cross_checks: Dict[Tuple[int, int], List[SignedProof]] = {}
        
        print("[VERIFY] Proof verification system initialized")
    
    def generate_worker_keypair(self) -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        """
        Generate a new Ed25519 keypair for a worker.
        Worker keeps private key secret, shares public key with network.
        """
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        return private_key, public_key
    
    def serialize_public_key(self, public_key: ed25519.Ed25519PublicKey) -> str:
        """Serialize public key to PEM format."""
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')
    
    def deserialize_public_key(self, pem: str) -> ed25519.Ed25519PublicKey:
        """Deserialize public key from PEM format."""
        public_key = serialization.load_pem_public_key(pem.encode('utf-8'))
        return public_key
    
    def register_worker_key(self, worker_id: str, public_key_pem: str):
        """Register a worker's public key."""
        try:
            public_key = self.deserialize_public_key(public_key_pem)
            self.worker_keys[worker_id] = public_key
            print(f"[VERIFY] Registered public key for worker {worker_id[:16]}...")
        except Exception as e:
            print(f"[VERIFY] Error registering key for worker {worker_id[:16]}...: {e}")
    
    def compute_proof_hash(self, proof_data: Dict) -> str:
        """
        Compute SHA-256 hash of proof data.
        Ensures integrity - any tampering changes the hash.
        """
        # Canonical JSON (sorted keys, no whitespace)
        canonical = json.dumps(proof_data, sort_keys=True, separators=(',', ':'))
        hash_bytes = hashlib.sha256(canonical.encode('utf-8')).digest()
        return hash_bytes.hex()
    
    def sign_proof(self, private_key: ed25519.Ed25519PrivateKey, 
                   proof_data: Dict) -> str:
        """
        Sign proof data with worker's private key.
        Returns signature as hex string.
        """
        # Compute hash
        proof_hash = self.compute_proof_hash(proof_data)
        hash_bytes = bytes.fromhex(proof_hash)
        
        # Sign the hash
        signature = private_key.sign(hash_bytes)
        return signature.hex()
    
    def verify_signature(self, public_key_pem: str, proof_data: Dict, 
                        signature_hex: str) -> bool:
        """
        Verify that signature matches proof data.
        Returns True if valid, False otherwise.
        """
        try:
            # Deserialize public key
            public_key = self.deserialize_public_key(public_key_pem)
            
            # Compute proof hash
            proof_hash = self.compute_proof_hash(proof_data)
            hash_bytes = bytes.fromhex(proof_hash)
            
            # Verify signature
            signature = bytes.fromhex(signature_hex)
            public_key.verify(signature, hash_bytes)
            
            return True
        except InvalidSignature:
            print(f"[VERIFY] ❌ Invalid signature detected!")
            return False
        except Exception as e:
            print(f"[VERIFY] Error verifying signature: {e}")
            return False
    
    def create_signed_proof(self, private_key: ed25519.Ed25519PrivateKey,
                           worker_id: str, range_start: int, range_end: int,
                           all_converged: bool, numbers_checked: int,
                           max_steps: int, compute_time: float,
                           ipfs_cid: str) -> SignedProof:
        """
        Create a signed proof from verification results.
        Worker calls this after completing verification.
        """
        # Prepare proof data (everything except signature)
        proof_data = {
            'worker_id': worker_id,
            'range_start': range_start,
            'range_end': range_end,
            'all_converged': all_converged,
            'numbers_checked': numbers_checked,
            'max_steps': max_steps,
            'compute_time': compute_time,
            'timestamp': time.time(),
            'ipfs_cid': ipfs_cid
        }
        
        # Compute hash
        proof_hash = self.compute_proof_hash(proof_data)
        
        # Sign the hash
        signature_hex = self.sign_proof(private_key, proof_data)
        
        # Get public key
        public_key = private_key.public_key()
        public_key_pem = self.serialize_public_key(public_key)
        
        # Create signed proof
        signed_proof = SignedProof(
            worker_id=worker_id,
            range_start=range_start,
            range_end=range_end,
            all_converged=all_converged,
            numbers_checked=numbers_checked,
            max_steps=max_steps,
            compute_time=compute_time,
            timestamp=proof_data['timestamp'],
            ipfs_cid=ipfs_cid,
            public_key_pem=public_key_pem,
            signature_hex=signature_hex,
            proof_hash=proof_hash
        )
        
        print(f"[VERIFY] ✅ Proof signed by worker {worker_id[:16]}...")
        print(f"[VERIFY] Proof hash: {proof_hash[:32]}...")
        
        return signed_proof
    
    def validate_proof(self, signed_proof: SignedProof) -> Tuple[bool, str]:
        """
        Validate a signed proof.
        Checks:
        1. Signature is valid
        2. Proof hash matches data
        3. Timestamp is reasonable
        4. Range is valid
        
        Returns (valid, error_message)
        """
        # Check signature
        proof_data = {
            'worker_id': signed_proof.worker_id,
            'range_start': signed_proof.range_start,
            'range_end': signed_proof.range_end,
            'all_converged': signed_proof.all_converged,
            'numbers_checked': signed_proof.numbers_checked,
            'max_steps': signed_proof.max_steps,
            'compute_time': signed_proof.compute_time,
            'timestamp': signed_proof.timestamp,
            'ipfs_cid': signed_proof.ipfs_cid
        }
        
        if not self.verify_signature(signed_proof.public_key_pem, proof_data, 
                                     signed_proof.signature_hex):
            return False, "Invalid cryptographic signature"
        
        # Check proof hash matches
        computed_hash = self.compute_proof_hash(proof_data)
        if computed_hash != signed_proof.proof_hash:
            return False, "Proof hash mismatch (data tampering detected)"
        
        # Check timestamp is reasonable (not future, not too old)
        current_time = time.time()
        if signed_proof.timestamp > current_time + 300:  # 5 min tolerance
            return False, "Timestamp is in the future"
        
        if current_time - signed_proof.timestamp > 86400 * 7:  # 7 days old
            return False, "Proof is too old (stale)"
        
        # Check range validity
        if signed_proof.range_start >= signed_proof.range_end:
            return False, "Invalid range (start >= end)"
        
        if signed_proof.range_start < 0:
            return False, "Invalid range (negative start)"
        
        # Check numbers_checked matches range
        expected_checked = (signed_proof.range_end - signed_proof.range_start) // 2
        if abs(signed_proof.numbers_checked - expected_checked) > expected_checked * 0.1:
            # Allow 10% variance (for odd/even boundaries)
            return False, f"Numbers checked ({signed_proof.numbers_checked}) doesn't match range"
        
        return True, "Proof is valid"
    
    def submit_for_consensus(self, signed_proof: SignedProof) -> Tuple[bool, str]:
        """
        Submit a signed proof for consensus checking.
        Integrates with trust system to determine consensus.
        """
        # First, validate the proof
        valid, error = self.validate_proof(signed_proof)
        if not valid:
            print(f"[VERIFY] ❌ Proof rejected: {error}")
            # Ban worker for submitting invalid proof
            if signed_proof.worker_id in self.trust_system.workers:
                stats = self.trust_system.workers[signed_proof.worker_id]
                stats.trust_level = TrustLevel.BANNED
                self.trust_system.save_state()
            return False, f"Proof validation failed: {error}"
        
        print(f"[VERIFY] ✅ Proof validated for worker {signed_proof.worker_id[:16]}...")
        
        # Create VerificationResult for trust system
        verification = VerificationResult(
            worker_id=signed_proof.worker_id,
            range_start=signed_proof.range_start,
            range_end=signed_proof.range_end,
            all_converged=signed_proof.all_converged,
            numbers_checked=signed_proof.numbers_checked,
            compute_time=signed_proof.compute_time,
            timestamp=signed_proof.timestamp,
            signature=signed_proof.signature_hex,
            proof_cid=signed_proof.ipfs_cid
        )
        
        # Submit to trust system for consensus
        consensus_reached, message = self.trust_system.submit_verification(verification)
        
        # Store for cross-checking
        range_key = (signed_proof.range_start, signed_proof.range_end)
        if range_key not in self.pending_cross_checks:
            self.pending_cross_checks[range_key] = []
        self.pending_cross_checks[range_key].append(signed_proof)
        
        return consensus_reached, message
    
    def get_proofs_for_range(self, range_start: int, range_end: int) -> List[SignedProof]:
        """Get all proofs submitted for a specific range."""
        range_key = (range_start, range_end)
        return self.pending_cross_checks.get(range_key, [])
    
    def detect_conflicts(self, range_start: int, range_end: int) -> Optional[List[SignedProof]]:
        """
        Check if there are conflicting results for a range.
        Returns list of conflicting proofs, or None if no conflict.
        """
        proofs = self.get_proofs_for_range(range_start, range_end)
        
        if len(proofs) < 2:
            return None  # Need at least 2 to have a conflict
        
        # Check if all results agree
        results = [p.all_converged for p in proofs]
        
        if len(set(results)) > 1:
            # Conflict detected!
            print(f"[VERIFY] ⚠️ CONFLICT DETECTED in range {range_start:,} - {range_end:,}")
            for proof in proofs:
                print(f"[VERIFY]   Worker {proof.worker_id[:16]}... says: {proof.all_converged}")
            return proofs
        
        return None
    
    def resolve_conflict_with_independent_verification(self, range_start: int, 
                                                       range_end: int,
                                                       correct_result: bool):
        """
        After independent verification, resolve conflict and update trust.
        Identifies which workers were correct and which were wrong.
        """
        proofs = self.get_proofs_for_range(range_start, range_end)
        
        correct_workers = []
        incorrect_workers = []
        
        for proof in proofs:
            if proof.all_converged == correct_result:
                correct_workers.append(proof.worker_id)
            else:
                incorrect_workers.append(proof.worker_id)
        
        # Update trust system
        self.trust_system.resolve_conflict(
            range_start, range_end, correct_result,
            correct_workers, incorrect_workers
        )
        
        # Remove from pending
        range_key = (range_start, range_end)
        if range_key in self.pending_cross_checks:
            del self.pending_cross_checks[range_key]
        
        print(f"[VERIFY] Conflict resolved. Correct: {len(correct_workers)}, Incorrect: {len(incorrect_workers)}")


# Example usage
if __name__ == "__main__":
    if not CRYPTO_AVAILABLE:
        print("Please install: pip install cryptography")
        exit(1)
    
    from trust_system import TrustSystem
    
    # Initialize systems
    trust = TrustSystem()
    verifier = ProofVerificationSystem(trust)
    
    # Generate keypair for a worker
    private_key, public_key = verifier.generate_worker_keypair()
    worker_id = "QmExampleWorker123"
    
    # Register worker
    public_key_pem = verifier.serialize_public_key(public_key)
    verifier.register_worker_key(worker_id, public_key_pem)
    
    # Create a signed proof
    signed_proof = verifier.create_signed_proof(
        private_key=private_key,
        worker_id=worker_id,
        range_start=1000000,
        range_end=1010000,
        all_converged=True,
        numbers_checked=5000,
        max_steps=10000,
        compute_time=15.5,
        ipfs_cid="QmExampleCID"
    )
    
    # Submit for consensus
    consensus, message = verifier.submit_for_consensus(signed_proof)
    print(f"\n{message}")
    
    # Show trust stats
    stats = trust.get_worker_stats(worker_id)
    if stats:
        print(f"\nWorker Stats:")
        print(f"  Trust Level: {stats.trust_level.name}")
        print(f"  Reputation: {stats.reputation_score:.1f}")
        print(f"  Verifications: {stats.total_verifications}")
