"""
IPFS LEADERBOARD GENERATOR
===========================
Generates HTML leaderboard webpage and publishes to IPFS/IPNS.

Auto-updates as users contribute. Shows:
- Top contributors by numbers checked
- Network statistics
- Active nodes
- Counterexample status
"""

import json
import time
from datetime import datetime
from typing import Dict, List
import ipfshttpclient

class LeaderboardGenerator:
    """Generates and publishes leaderboard to IPFS."""
    
    def __init__(self, ipfs_api: str = '/ip4/127.0.0.1/tcp/5001'):
        """Initialize leaderboard generator."""
        self.client = ipfshttpclient.connect(ipfs_api)
        self.node_id = self.client.id()['ID']
    
    def generate_leaderboard_html(self, user_stats: List[Dict], 
                                   network_stats: Dict,
                                   genesis_timestamp: str = None) -> str:
        """
        Generate HTML leaderboard page.
        
        Args:
            user_stats: List of user statistics dicts
            network_stats: Network-wide statistics
            genesis_timestamp: When network started
            
        Returns:
            HTML string
        """
        # Sort users by total numbers checked
        user_stats_sorted = sorted(user_stats, 
                                   key=lambda u: u.get('total_numbers_checked', 0),
                                   reverse=True)
        
        # Build leaderboard rows
        leaderboard_rows = ""
        for rank, user in enumerate(user_stats_sorted[:100], 1):  # Top 100
            username = user.get('username', 'Anonymous')
            numbers = user.get('total_numbers_checked', 0)
            ranges = user.get('total_ranges_completed', 0)
            compute_time = user.get('total_compute_time', 0)
            nodes = user.get('num_nodes', 1)
            
            # Medal for top 3
            medal = ""
            if rank == 1:
                medal = "🥇"
            elif rank == 2:
                medal = "🥈"
            elif rank == 3:
                medal = "🥉"
            
            leaderboard_rows += f"""
            <tr>
                <td class="rank">{medal} {rank}</td>
                <td class="username">{username}</td>
                <td class="numbers">{numbers:,}</td>
                <td class="ranges">{ranges:,}</td>
                <td class="time">{compute_time:.1f}s</td>
                <td class="nodes">{nodes}</td>
            </tr>
            """
        
        # Calculate network duration
        duration_str = "Unknown"
        if genesis_timestamp:
            try:
                genesis = datetime.fromisoformat(genesis_timestamp)
                now = datetime.now()
                duration = now - genesis
                days = duration.days
                hours = duration.seconds // 3600
                duration_str = f"{days}d {hours}h"
            except:
                pass
        
        # Build HTML
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="300">
    <title>Collatz Distributed Network - Leaderboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        
        h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.8;
        }}
        
        .leaderboard {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
        }}
        
        th {{
            padding: 20px;
            text-align: left;
            font-weight: 600;
            font-size: 1.1em;
        }}
        
        tbody tr {{
            border-bottom: 1px solid #e0e0e0;
            transition: background 0.2s;
        }}
        
        tbody tr:hover {{
            background: rgba(102, 126, 234, 0.1);
        }}
        
        td {{
            padding: 15px 20px;
            color: #333;
        }}
        
        .rank {{
            font-weight: bold;
            font-size: 1.2em;
        }}
        
        .username {{
            font-weight: 600;
            color: #667eea;
        }}
        
        .numbers {{
            font-family: 'Courier New', monospace;
            color: #4caf50;
        }}
        
        footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            opacity: 0.8;
        }}
        
        .update-time {{
            font-size: 0.9em;
            margin-top: 10px;
        }}
        
        .counterexample-alert {{
            background: #ff4444;
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 20px;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔢 Collatz Conjecture</h1>
            <div class="subtitle">Distributed Verification Network</div>
        </header>
        
        {'<div class="counterexample-alert">🎉 COUNTEREXAMPLE FOUND! 🎉</div>' if network_stats.get('counterexample_found') else ''}
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{network_stats.get('active_workers', 0)}</div>
                <div class="stat-label">Active Nodes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{network_stats.get('global_highest_proven', 0):,}</div>
                <div class="stat-label">Highest Verified</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(user_stats_sorted)}</div>
                <div class="stat-label">Contributors</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{duration_str}</div>
                <div class="stat-label">Network Uptime</div>
            </div>
        </div>
        
        <div class="leaderboard">
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Username</th>
                        <th>Numbers Checked</th>
                        <th>Ranges Completed</th>
                        <th>Compute Time</th>
                        <th>Nodes</th>
                    </tr>
                </thead>
                <tbody>
                    {leaderboard_rows}
                </tbody>
            </table>
        </div>
        
        <footer>
            <div>Join the network and contribute to mathematical history!</div>
            <div class="update-time">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
            <div class="update-time">Auto-refreshes every 5 minutes</div>
        </footer>
    </div>
</body>
</html>
"""
        return html
    
    def publish_leaderboard(self, html: str) -> str:
        """
        Publish leaderboard HTML to IPFS.
        
        Args:
            html: HTML content to publish
            
        Returns:
            IPFS CID
        """
        # Upload to IPFS
        result = self.client.add_str(html)
        cid = result
        
        print(f"[LEADERBOARD] Published to IPFS: /ipfs/{cid}")
        
        # Try to publish to IPNS for persistent URL
        try:
            self.client.name.publish(cid, key='collatz-leaderboard', lifetime='24h')
            print(f"[LEADERBOARD] Published to IPNS: /ipns/collatz-leaderboard")
        except Exception as e:
            print(f"[LEADERBOARD] IPNS publish failed: {e}")
        
        return cid
    
    def update_leaderboard(self):
        """
        Update leaderboard from current network state.
        Reads user_accounts.json and coordinator state.
        """
        try:
            # Load user accounts
            try:
                with open('user_accounts.json', 'r') as f:
                    accounts_data = json.load(f)
                user_stats = list(accounts_data.get('users', {}).values())
            except FileNotFoundError:
                user_stats = []
            
            # Get network statistics
            from ipfs_coordinator import IPFSCoordinator
            coordinator = IPFSCoordinator()
            network_stats = coordinator.get_network_statistics()
            genesis_timestamp = getattr(coordinator, 'genesis_timestamp', None)
            
            # Generate HTML
            html = self.generate_leaderboard_html(user_stats, network_stats, genesis_timestamp)
            
            # Publish to IPFS
            cid = self.publish_leaderboard(html)
            
            print(f"[LEADERBOARD] ✅ Leaderboard updated!")
            print(f"[LEADERBOARD] View at: https://ipfs.io/ipfs/{cid}")
            
            return cid
            
        except Exception as e:
            print(f"[LEADERBOARD] Error updating: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    """Generate and publish leaderboard."""
    generator = LeaderboardGenerator()
    generator.update_leaderboard()
