#!/usr/bin/env python3
"""
Production Initialization Script

This script prepares the Collatz distributed system for production deployment.
It resets the verification state to require cluster consensus on all existing progress.

IMPORTANT: Run this ONCE before deploying to production!
"""

import json
from datetime import datetime
import sys

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def reset_for_production():
    """
    Reset the system for production:
    1. Mark all progress above 2^71 as verified by 'node_1' (requires cluster verification)
    2. Set genesis timestamp for the network
    3. Clear any testing artifacts
    """
    
    # Define the production starting point
    PRODUCTION_START = 2**71  # 2,361,183,241,434,822,606,848
    
    print("=" * 70)
    print("COLLATZ DISTRIBUTED NETWORK - PRODUCTION INITIALIZATION")
    print("=" * 70)
    
    # Read current progress
    try:
        with open('collatz_config.json', 'r') as f:
            config = json.load(f)
        current_highest = config.get('highest_proven', 0)
        print(f"\n[DATA] Current highest proven: {current_highest:,}")
    except FileNotFoundError:
        current_highest = PRODUCTION_START
        print("\n[DATA] No existing config found, starting fresh")
    
    # Reset to production state
    production_config = {
        "highest_proven": PRODUCTION_START,
        "total_tested": 0,  # Will be recalculated from verified work
        "total_runtime_seconds": 0.0,
        "max_steps_ever": 0,
        "last_updated": datetime.now().isoformat(),
        "production_mode": True,
        "genesis_timestamp": datetime.now().isoformat(),
        "genesis_node": "node_1"  # First node that started the network
    }
    
    # If we had progress beyond 2^71, note it needs verification
    if current_highest > PRODUCTION_START:
        numbers_needing_verification = current_highest - PRODUCTION_START
        print(f"\n[WARNING] RESETTING FOR PRODUCTION:")
        print(f"   Previous highest: {current_highest:,}")
        print(f"   New starting point: {PRODUCTION_START:,}")
        print(f"   Numbers needing cluster verification: {numbers_needing_verification:,}")
        print(f"\n   These numbers were verified during testing by node_1")
        print(f"   and will require cluster consensus (3+ workers) in production.")
    
    # Save production config
    with open('collatz_config.json', 'w') as f:
        json.dump(production_config, f, indent=2)
    
    print(f"\n[SUCCESS] Production config saved!")
    print(f"   Starting point: {PRODUCTION_START:,} (2^71)")
    print(f"   Genesis timestamp: {production_config['genesis_timestamp']}")
    
    # Initialize IPFS coordinator state for production
    coordinator_state = {
        "network_state": {
            "global_highest_proven": PRODUCTION_START,
            "work_frontier": [],  # Will be populated by first node
            "total_work_generated": 0,
            "total_work_completed": 0,
            "network_mode": "fully_decentralized",
            "production_mode": True,
            "genesis_timestamp": production_config['genesis_timestamp'],
            "genesis_node": "node_1",
            "counterexample_found": False,
            "counterexample_data": None,
            "network_voting": {
                "active": False,
                "question": "",
                "votes": {},
                "required_majority": 0.5
            }
        },
        "known_peers": [],
        "last_sync": None
    }
    
    # Note: Don't write coordinator_state.json here - let first node initialize it
    # This prevents conflicts with IPFS coordination
    
    print("\n[NEXT STEPS]")
    print("   1. Start IPFS daemon: ipfs daemon")
    print("   2. Launch first worker node (will become genesis node)")
    print("   3. User will be prompted to create account on first run")
    print("   4. Network begins from 2^71 with full cluster verification")
    
    print("\n" + "=" * 70)
    print("READY FOR PRODUCTION DEPLOYMENT")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    reset_for_production()
