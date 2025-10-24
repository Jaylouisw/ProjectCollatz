"""
Collatz Engine - Contribution Tracker
Tracks and verifies contributions from different users/machines

Copyright (c) 2025 Jay (CollatzEngine)
Licensed under CC BY-NC-SA 4.0
https://creativecommons.org/licenses/by-nc-sa/4.0/
"""

import json
import hashlib
import platform
import socket
from datetime import datetime
import os

CONTRIBUTIONS_FILE = "contributions.json"

def get_machine_id():
    """Generate a unique machine identifier."""
    # Use hostname + platform info for ID
    hostname = socket.gethostname()
    platform_info = f"{platform.system()}_{platform.machine()}"
    
    # Create a hash for privacy
    machine_string = f"{hostname}_{platform_info}"
    machine_hash = hashlib.sha256(machine_string.encode()).hexdigest()[:16]
    
    return machine_hash

def get_user_info():
    """Get user/contributor information."""
    machine_id = get_machine_id()
    
    # Load or create user profile
    profile_file = "user_profile.json"
    if os.path.exists(profile_file):
        with open(profile_file, 'r') as f:
            profile = json.load(f)
    else:
        # First run - collect user info
        print("=" * 70)
        print("FIRST RUN - CONTRIBUTOR SETUP")
        print("=" * 70)
        print("Your contributions will be tracked and can be shared with the community!")
        print("This helps build a distributed verification network.")
        print()
        
        username = input("Enter your username/alias (or press Enter to use machine ID): ").strip()
        if not username:
            username = f"User_{machine_id[:8]}"
        
        gpu_name = input("GPU name (e.g., 'RTX 3060') [optional]: ").strip()
        
        profile = {
            "username": username,
            "machine_id": machine_id,
            "gpu_name": gpu_name,
            "created": datetime.now().isoformat(),
            "hostname": socket.gethostname(),
            "platform": platform.system()
        }
        
        with open(profile_file, 'w') as f:
            json.dump(profile, f, indent=2)
        
        print()
        print(f"Profile created! Contributing as: {username}")
        print("=" * 70)
        print()
    
    return profile

def load_contributions():
    """Load existing contributions."""
    if os.path.exists(CONTRIBUTIONS_FILE):
        with open(CONTRIBUTIONS_FILE, 'r') as f:
            return json.load(f)
    else:
        return {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "contributors": {},
            "verified_ranges": []
        }

def save_contributions(data):
    """Save contributions to file."""
    with open(CONTRIBUTIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_contribution(highest_proven, total_tested, session_tested, runtime_seconds):
    """Record a contribution from current session."""
    profile = get_user_info()
    contributions = load_contributions()
    
    username = profile["username"]
    machine_id = profile["machine_id"]
    
    # Initialize contributor if new
    if username not in contributions["contributors"]:
        contributions["contributors"][username] = {
            "machine_id": machine_id,
            "gpu_name": profile.get("gpu_name", "Unknown"),
            "first_contribution": datetime.now().isoformat(),
            "total_numbers_tested": 0,
            "total_runtime_hours": 0,
            "sessions": []
        }
    
    contributor = contributions["contributors"][username]
    
    # Add session data
    session = {
        "timestamp": datetime.now().isoformat(),
        "highest_proven": str(highest_proven),
        "session_tested": str(session_tested),
        "runtime_seconds": runtime_seconds,
        "machine_id": machine_id
    }
    
    contributor["sessions"].append(session)
    contributor["total_numbers_tested"] = str(int(contributor["total_numbers_tested"]) + session_tested)
    contributor["total_runtime_hours"] = contributor["total_runtime_hours"] + (runtime_seconds / 3600)
    contributor["last_contribution"] = datetime.now().isoformat()
    
    # Update verified ranges (track highest values proven by anyone)
    existing_range = None
    for vr in contributions["verified_ranges"]:
        if vr["contributor"] == username:
            existing_range = vr
            break
    
    if existing_range:
        # Update if this is higher
        if highest_proven > int(existing_range["highest_proven"]):
            existing_range["highest_proven"] = str(highest_proven)
            existing_range["last_updated"] = datetime.now().isoformat()
    else:
        # Add new range
        contributions["verified_ranges"].append({
            "contributor": username,
            "highest_proven": str(highest_proven),
            "machine_id": machine_id,
            "first_verified": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        })
    
    # Sort verified ranges by highest proven (descending)
    contributions["verified_ranges"].sort(key=lambda x: int(x["highest_proven"]), reverse=True)
    
    save_contributions(contributions)
    
    return username

def get_contribution_summary():
    """Get summary of all contributions."""
    if not os.path.exists(CONTRIBUTIONS_FILE):
        return None
    
    contributions = load_contributions()
    
    summary = {
        "total_contributors": len(contributions["contributors"]),
        "total_numbers_tested": 0,
        "total_runtime_hours": 0,
        "highest_proven_overall": 0,
        "top_contributors": []
    }
    
    for username, data in contributions["contributors"].items():
        total_tested = int(data["total_numbers_tested"])
        summary["total_numbers_tested"] += total_tested
        summary["total_runtime_hours"] += data["total_runtime_hours"]
        
        summary["top_contributors"].append({
            "username": username,
            "total_tested": total_tested,
            "runtime_hours": data["total_runtime_hours"],
            "sessions": len(data["sessions"]),
            "gpu": data.get("gpu_name", "Unknown")
        })
    
    # Sort by total tested
    summary["top_contributors"].sort(key=lambda x: x["total_tested"], reverse=True)
    
    # Get highest proven overall
    if contributions["verified_ranges"]:
        summary["highest_proven_overall"] = int(contributions["verified_ranges"][0]["highest_proven"])
    
    return summary

def print_contribution_leaderboard():
    """Print a leaderboard of all contributors."""
    summary = get_contribution_summary()
    
    if not summary:
        print("No contributions recorded yet.")
        return
    
    print()
    print("=" * 70)
    print("COLLATZ ENGINE - CONTRIBUTION LEADERBOARD")
    print("=" * 70)
    print()
    print(f"Total Contributors: {summary['total_contributors']}")
    print(f"Total Numbers Tested: {summary['total_numbers_tested']:,}")
    print(f"Total Runtime: {summary['total_runtime_hours']:.1f} hours")
    print(f"Highest Proven Overall: {summary['highest_proven_overall']:,}")
    print()
    print("TOP CONTRIBUTORS:")
    print("-" * 70)
    print(f"{'Rank':<6} {'Username':<20} {'Numbers Tested':<20} {'Runtime':<12} {'GPU':<15}")
    print("-" * 70)
    
    for i, contrib in enumerate(summary["top_contributors"][:10], 1):
        print(f"{i:<6} {contrib['username']:<20} {contrib['total_tested']:>19,} "
              f"{contrib['runtime_hours']:>10.1f}h {contrib['gpu']:<15}")
    
    print("=" * 70)
    print()

def export_contributions(filename="contributions_export.json"):
    """Export contributions in a shareable format."""
    contributions = load_contributions()
    
    # Create export data (anonymize machine IDs for privacy)
    export_data = {
        "exported": datetime.now().isoformat(),
        "version": contributions["version"],
        "summary": get_contribution_summary(),
        "verified_ranges": [
            {
                "contributor": vr["contributor"],
                "highest_proven": vr["highest_proven"],
                "last_updated": vr["last_updated"]
            }
            for vr in contributions["verified_ranges"]
        ]
    }
    
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"Contributions exported to: {filename}")
    print("You can share this file with the community!")
    
    return filename

def merge_contributions(import_file):
    """Merge contributions from another file (from another user)."""
    if not os.path.exists(import_file):
        print(f"File not found: {import_file}")
        return
    
    with open(import_file, 'r') as f:
        imported = json.load(f)
    
    local = load_contributions()
    
    # Merge contributors (avoid duplicates by machine_id)
    merged_count = 0
    for username, data in imported.get("contributors", {}).items():
        machine_id = data.get("machine_id", "unknown")
        
        # Check if this contributor already exists
        exists = False
        for local_username, local_data in local["contributors"].items():
            if local_data.get("machine_id") == machine_id:
                exists = True
                # Merge sessions if same contributor
                if local_username == username:
                    existing_session_times = {s["timestamp"] for s in local_data["sessions"]}
                    for session in data["sessions"]:
                        if session["timestamp"] not in existing_session_times:
                            local_data["sessions"].append(session)
                            merged_count += 1
                break
        
        if not exists:
            local["contributors"][username] = data
            merged_count += 1
    
    # Merge verified ranges
    for vr in imported.get("verified_ranges", []):
        existing = False
        for local_vr in local["verified_ranges"]:
            if local_vr["contributor"] == vr["contributor"] and local_vr["machine_id"] == vr["machine_id"]:
                # Update if higher
                if int(vr["highest_proven"]) > int(local_vr["highest_proven"]):
                    local_vr["highest_proven"] = vr["highest_proven"]
                    local_vr["last_updated"] = vr["last_updated"]
                existing = True
                break
        
        if not existing:
            local["verified_ranges"].append(vr)
    
    # Re-sort verified ranges
    local["verified_ranges"].sort(key=lambda x: int(x["highest_proven"]), reverse=True)
    
    save_contributions(local)
    
    print(f"Successfully merged {merged_count} new contributions!")
    print_contribution_leaderboard()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "leaderboard":
            print_contribution_leaderboard()
        elif command == "export":
            export_contributions()
        elif command == "merge" and len(sys.argv) > 2:
            merge_contributions(sys.argv[2])
        elif command == "summary":
            summary = get_contribution_summary()
            if summary:
                print(json.dumps(summary, indent=2))
            else:
                print("No contributions recorded yet.")
        else:
            print("Usage:")
            print("  python contribution_tracker.py leaderboard   - Show contributor rankings")
            print("  python contribution_tracker.py export        - Export contributions for sharing")
            print("  python contribution_tracker.py merge <file>  - Merge contributions from another user")
            print("  python contribution_tracker.py summary       - Show JSON summary")
    else:
        print_contribution_leaderboard()
