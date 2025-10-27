"""
DISTRIBUTED COLLATZ - USER ACCOUNT SYSTEM
==========================================
Copyright (c) 2025 Jay Wenden (CollatzEngine)
Licensed under CC BY-NC-SA 4.0

User account management for distributed verification network.
Links multiple worker nodes to a single user identity.
Tracks contributions across all nodes belonging to a user.

Features:
- Ed25519-based user authentication
- Multiple nodes per user account
- Persistent identity across sessions
- Contribution aggregation per user
- Public reputation tied to username
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    from cryptography.exceptions import InvalidSignature
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("[ACCOUNT] cryptography not installed. Run: pip install cryptography")


@dataclass
class UserAccount:
    """User account in the distributed network."""
    username: str
    user_id: str  # Derived from public key hash
    public_key_pem: str
    registered_nodes: List[str]  # Worker node IDs
    created_at: float
    last_active: float
    total_contributions: int = 0  # Total numbers verified
    total_ranges: int = 0  # Total ranges completed
    total_compute_hours: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserAccount':
        """Create from dictionary."""
        return cls(**data)


class UserAccountManager:
    """Manages user accounts in the distributed network."""
    
    def __init__(self, storage_dir: str = "."):
        """Initialize account manager."""
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography library required")
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Create keys directory for private keys
        self.keys_dir = Path("keys")
        self.keys_dir.mkdir(exist_ok=True)
        
        # Local cache of accounts
        self.accounts: Dict[str, UserAccount] = {}
        
        # Account database file
        self.db_file = self.storage_dir / "user_accounts.json"
        
        self.load_accounts()
        
        print("[ACCOUNT] User account manager initialized")
    
    def load_accounts(self):
        """Load all user accounts from storage."""
        try:
            if self.db_file.exists():
                with open(self.db_file, 'r') as f:
                    data = json.load(f)
                    for user_id, account_data in data.items():
                        self.accounts[user_id] = UserAccount.from_dict(account_data)
                print(f"[ACCOUNT] Loaded {len(self.accounts)} user accounts")
        except Exception as e:
            print(f"[ACCOUNT] Error loading accounts: {e}")
    
    def save_accounts(self):
        """Save all user accounts to storage."""
        try:
            data = {
                user_id: account.to_dict()
                for user_id, account in self.accounts.items()
            }
            with open(self.db_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ACCOUNT] Error saving accounts: {e}")
    
    def generate_user_id(self, public_key: ed25519.Ed25519PublicKey) -> str:
        """
        Generate deterministic user ID from public key.
        This ensures same public key always gets same user ID.
        """
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        user_id_hash = hashlib.sha256(public_bytes).hexdigest()
        return f"U{user_id_hash[:16]}"  # U + first 16 hex chars
    
    def create_user_account(self, username: str, 
                           private_key_path: Optional[str] = None) -> Tuple[UserAccount, ed25519.Ed25519PrivateKey]:
        """
        Create a new user account with keypair.
        
        Args:
            username: Desired username (must be unique)
            private_key_path: Path to save private key (default: username_key.pem)
        
        Returns:
            (UserAccount, private_key)
        """
        # Check if username already taken
        for account in self.accounts.values():
            if account.username.lower() == username.lower():
                raise ValueError(f"Username '{username}' already taken")
        
        # Generate keypair
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        # Generate user ID from public key
        user_id = self.generate_user_id(public_key)
        
        # Serialize public key
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        # Create account
        account = UserAccount(
            username=username,
            user_id=user_id,
            public_key_pem=public_key_pem,
            registered_nodes=[],
            created_at=time.time(),
            last_active=time.time()
        )
        
        self.accounts[user_id] = account
        self.save_accounts()
        
        # Save private key in keys/ directory
        if private_key_path is None:
            private_key_path = str(self.keys_dir / f"{username}_private_key.pem")
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        with open(private_key_path, 'wb') as f:
            f.write(private_pem)
        
        print(f"[ACCOUNT] ✅ Created user account: {username}")
        print(f"[ACCOUNT] User ID: {user_id}")
        print(f"[ACCOUNT] Private key saved to: {private_key_path}")
        print(f"[ACCOUNT] ⚠️ BACKUP THIS FILE! It's your identity across all nodes.")
        
        return account, private_key
    
    def load_user_account(self, private_key_path: str) -> Tuple[UserAccount, ed25519.Ed25519PrivateKey]:
        """
        Load existing user account from private key file.
        
        Args:
            private_key_path: Path to private key PEM file
        
        Returns:
            (UserAccount, private_key)
        """
        # Load private key
        with open(private_key_path, 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None
            )
        
        public_key = private_key.public_key()
        user_id = self.generate_user_id(public_key)
        
        # Find account
        if user_id not in self.accounts:
            raise ValueError(f"No account found for this private key (ID: {user_id})")
        
        account = self.accounts[user_id]
        account.last_active = time.time()
        self.save_accounts()
        
        print(f"[ACCOUNT] ✅ Loaded user account: {account.username}")
        print(f"[ACCOUNT] User ID: {user_id}")
        
        return account, private_key
    
    def register_node(self, user_id: str, node_id: str):
        """Register a worker node to a user account."""
        if user_id not in self.accounts:
            raise ValueError(f"User ID {user_id} not found")
        
        account = self.accounts[user_id]
        
        if node_id not in account.registered_nodes:
            account.registered_nodes.append(node_id)
            account.last_active = time.time()
            self.save_accounts()
            
            print(f"[ACCOUNT] Node {node_id[:16]}... registered to user {account.username}")
    
    def update_contributions(self, user_id: str, numbers_checked: int, 
                            ranges_completed: int, compute_time: float):
        """Update user's contribution statistics."""
        if user_id not in self.accounts:
            return
        
        account = self.accounts[user_id]
        account.total_contributions += numbers_checked
        account.total_ranges += ranges_completed
        account.total_compute_hours += compute_time / 3600
        account.last_active = time.time()
        
        self.save_accounts()
    
    def get_account_by_username(self, username: str) -> Optional[UserAccount]:
        """Get account by username."""
        for account in self.accounts.values():
            if account.username.lower() == username.lower():
                return account
        return None
    
    def get_account_by_user_id(self, user_id: str) -> Optional[UserAccount]:
        """Get account by user ID."""
        return self.accounts.get(user_id)
    
    def get_account_by_node_id(self, node_id: str) -> Optional[UserAccount]:
        """Get account that owns a specific node."""
        for account in self.accounts.values():
            if node_id in account.registered_nodes:
                return account
        return None
    
    def get_leaderboard(self, top_n: int = 10) -> List[UserAccount]:
        """Get top users by total contributions."""
        sorted_users = sorted(
            self.accounts.values(),
            key=lambda a: a.total_contributions,
            reverse=True
        )
        return sorted_users[:top_n]
    
    def get_statistics(self) -> Dict:
        """Get network-wide user statistics."""
        if not self.accounts:
            return {
                'total_users': 0,
                'active_users_24h': 0,
                'total_contributions': 0,
                'total_compute_hours': 0
            }
        
        active_cutoff = time.time() - 86400  # 24 hours
        active_users = sum(1 for a in self.accounts.values() if a.last_active > active_cutoff)
        
        return {
            'total_users': len(self.accounts),
            'active_users_24h': active_users,
            'total_nodes': sum(len(a.registered_nodes) for a in self.accounts.values()),
            'total_contributions': sum(a.total_contributions for a in self.accounts.values()),
            'total_ranges': sum(a.total_ranges for a in self.accounts.values()),
            'total_compute_hours': sum(a.total_compute_hours for a in self.accounts.values())
        }
    
    def sign_message(self, private_key: ed25519.Ed25519PrivateKey, message: str) -> str:
        """Sign a message with user's private key."""
        message_bytes = message.encode('utf-8')
        signature = private_key.sign(message_bytes)
        return signature.hex()
    
    def verify_message(self, user_id: str, message: str, signature_hex: str) -> bool:
        """Verify a message was signed by a specific user."""
        if user_id not in self.accounts:
            return False
        
        account = self.accounts[user_id]
        
        try:
            # Load public key
            public_key = serialization.load_pem_public_key(
                account.public_key_pem.encode('utf-8')
            )
            
            # Verify signature
            message_bytes = message.encode('utf-8')
            signature = bytes.fromhex(signature_hex)
            public_key.verify(signature, message_bytes)
            
            return True
        except (InvalidSignature, Exception):
            return False
    
    def export_account_to_ipfs(self, user_id: str) -> Dict:
        """
        Export account data for IPFS publication.
        Public information only (no private keys).
        """
        if user_id not in self.accounts:
            raise ValueError(f"User ID {user_id} not found")
        
        account = self.accounts[user_id]
        
        return {
            'username': account.username,
            'user_id': account.user_id,
            'public_key_pem': account.public_key_pem,
            'registered_nodes': account.registered_nodes,
            'created_at': account.created_at,
            'last_active': account.last_active,
            'total_contributions': account.total_contributions,
            'total_ranges': account.total_ranges,
            'total_compute_hours': account.total_compute_hours
        }
    
    def import_account_from_ipfs(self, account_data: Dict):
        """
        Import account data from IPFS.
        Merges with existing account if already present.
        """
        user_id = account_data['user_id']
        
        if user_id in self.accounts:
            # Merge contributions (take maximum)
            existing = self.accounts[user_id]
            existing.total_contributions = max(existing.total_contributions, 
                                              account_data['total_contributions'])
            existing.total_ranges = max(existing.total_ranges, 
                                       account_data['total_ranges'])
            existing.total_compute_hours = max(existing.total_compute_hours, 
                                              account_data['total_compute_hours'])
            existing.last_active = max(existing.last_active, 
                                      account_data['last_active'])
            
            # Merge node lists
            for node_id in account_data['registered_nodes']:
                if node_id not in existing.registered_nodes:
                    existing.registered_nodes.append(node_id)
        else:
            # Create new account
            self.accounts[user_id] = UserAccount.from_dict(account_data)
        
        self.save_accounts()


# CLI for user management
def main():
    """Command-line interface for user account management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Distributed Collatz User Account Manager")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create account
    create_parser = subparsers.add_parser('create', help='Create new user account')
    create_parser.add_argument('username', help='Desired username')
    
    # Load account
    load_parser = subparsers.add_parser('load', help='Load existing account')
    load_parser.add_argument('keyfile', help='Path to private key file')
    
    # Show stats
    stats_parser = subparsers.add_parser('stats', help='Show account statistics')
    stats_parser.add_argument('username', nargs='?', help='Username (omit for all)')
    
    # Leaderboard
    subparsers.add_parser('leaderboard', help='Show top contributors')
    
    args = parser.parse_args()
    
    if not CRYPTO_AVAILABLE:
        print("Error: cryptography library not installed")
        print("Install with: pip install cryptography")
        return 1
    
    manager = UserAccountManager()
    
    if args.command == 'create':
        try:
            account, private_key = manager.create_user_account(args.username)
            print(f"\n✅ Account created successfully!")
            print(f"Username: {account.username}")
            print(f"User ID: {account.user_id}")
            print(f"\nUse this private key file when starting worker nodes.")
        except ValueError as e:
            print(f"Error: {e}")
            return 1
    
    elif args.command == 'load':
        try:
            account, private_key = manager.load_user_account(args.keyfile)
            print(f"\n✅ Account loaded successfully!")
            print(f"Username: {account.username}")
            print(f"Nodes: {len(account.registered_nodes)}")
            print(f"Contributions: {account.total_contributions:,} numbers")
            print(f"Compute time: {account.total_compute_hours:.1f} hours")
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    elif args.command == 'stats':
        if args.username:
            account = manager.get_account_by_username(args.username)
            if account:
                print(f"\nUser: {account.username}")
                print(f"User ID: {account.user_id}")
                print(f"Nodes: {len(account.registered_nodes)}")
                print(f"Contributions: {account.total_contributions:,} numbers")
                print(f"Ranges: {account.total_ranges:,}")
                print(f"Compute time: {account.total_compute_hours:.1f} hours")
                print(f"Created: {time.strftime('%Y-%m-%d', time.localtime(account.created_at))}")
                print(f"Last active: {time.strftime('%Y-%m-%d %H:%M', time.localtime(account.last_active))}")
            else:
                print(f"User '{args.username}' not found")
        else:
            stats = manager.get_statistics()
            print(f"\nNetwork Statistics:")
            print(f"Total users: {stats['total_users']}")
            print(f"Active (24h): {stats['active_users_24h']}")
            print(f"Total nodes: {stats['total_nodes']}")
            print(f"Total contributions: {stats['total_contributions']:,} numbers")
            print(f"Total ranges: {stats['total_ranges']:,}")
            print(f"Total compute time: {stats['total_compute_hours']:.1f} hours")
    
    elif args.command == 'leaderboard':
        top = manager.get_leaderboard(10)
        print(f"\n🏆 Top Contributors:")
        for i, account in enumerate(top, 1):
            print(f"{i:2}. {account.username:20} - {account.total_contributions:15,} numbers - "
                  f"{account.total_compute_hours:8.1f}h - {len(account.registered_nodes)} nodes")
    
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
