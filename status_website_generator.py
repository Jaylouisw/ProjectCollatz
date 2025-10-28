"""
Status Website Generator for ProjectCollatz
Generates a lightweight HTML status page and publishes to IPFS.
"""
import time
import json
from datetime import datetime, timezone
from typing import Dict, Optional
import ipfshttpclient


def format_duration(seconds: float) -> str:
    """Format seconds into years, months, weeks, days, hours, minutes."""
    secs = int(seconds)
    years, secs = divmod(secs, 365 * 24 * 3600)
    months, secs = divmod(secs, 30 * 24 * 3600)
    weeks, secs = divmod(secs, 7 * 24 * 3600)
    days, secs = divmod(secs, 24 * 3600)
    hours, secs = divmod(secs, 3600)
    minutes, secs = divmod(secs, 60)

    parts = []
    if years: parts.append(f"{years}y")
    if months: parts.append(f"{months}mo")
    if weeks: parts.append(f"{weeks}w")
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    if not parts:
        parts.append("0m")
    return ' '.join(parts)


class StatusWebsiteGenerator:
    """Generates and publishes a simple status website for ProjectCollatz."""

    def __init__(self, ipfs_api: str = '/ip4/127.0.0.1/tcp/5001'):
        self.client = ipfshttpclient.connect(ipfs_api)
        self.node_id = self.client.id()['ID']

    def generate_status_html(self, network_stats: Dict, active_nodes: int, rate: float,
                             leaderboard_cid: Optional[str], genesis_timestamp: Optional[str]) -> str:
        now = datetime.now(timezone.utc)
        genesis = None
        if genesis_timestamp:
            try:
                genesis = datetime.fromisoformat(genesis_timestamp)
            except Exception:
                try:
                    genesis = datetime.fromtimestamp(float(genesis_timestamp), tz=timezone.utc)
                except Exception:
                    genesis = None

        runtime_str = "Unknown"
        if genesis:
            runtime_seconds = (now - genesis).total_seconds()
            runtime_str = format_duration(runtime_seconds)

        leaderboard_link = f"https://ipfs.io/ipfs/{leaderboard_cid}" if leaderboard_cid else "(not available)"

        html = f"""
        <!doctype html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>ProjectCollatz Status</title>
          <meta name="viewport" content="width=device-width,initial-scale=1">
          <style>
            body{{font-family:system-ui,Arial,Helvetica,sans-serif;margin:24px;color:#111}}
            header{{margin-bottom:18px}}
            .card{{padding:12px;border-radius:8px;border:1px solid #eee;margin-bottom:12px}}
            .stat{{font-size:24px;font-weight:600}}
          </style>
        </head>
        <body>
          <header>
            <h1>ProjectCollatz — Network Status</h1>
            <p>Node: {self.node_id[:16]}...</p>
          </header>

          <section class="card">
            <div>Network Runtime: <span class="stat">{runtime_str}</span></div>
            <div>Active nodes: <span class="stat">{active_nodes}</span></div>
            <div>Current verification rate: <span class="stat">{rate:,} odd/sec</span></div>
          </section>

          <section class="card">
            <h3>Network statistics</h3>
            <pre>{json.dumps(network_stats, indent=2)}</pre>
          </section>

          <section class="card">
            <h3>Leaderboard</h3>
            <p><a href="{leaderboard_link}" target="_blank">View leaderboard</a></p>
          </section>

          <footer><small>Last updated: {now.isoformat()}</small></footer>
        </body>
        </html>
        """

        return html

    def update_status(self, network_stats: Dict, leaderboard_cid: Optional[str], active_nodes: int, node_id: str) -> Optional[str]:
        try:
            # Estimate rate from network_stats if provided
            rate = network_stats.get('average_rate', 0) if isinstance(network_stats, dict) else 0
            genesis_timestamp = network_stats.get('genesis_timestamp') if isinstance(network_stats, dict) else None

            html = self.generate_status_html(network_stats, active_nodes, rate, leaderboard_cid, genesis_timestamp)
            cid = self.client.add_str(html)

            # Try publishing to IPNS key 'collatz-status' if exists
            try:
                self.client.name.publish(cid, key='collatz-status', lifetime='24h')
            except Exception:
                pass

            print(f"[STATUS] Published to IPFS: /ipfs/{cid}")
            return cid
        except Exception as e:
            print(f"[STATUS] Error generating status: {e}")
            return None


if __name__ == '__main__':
    g = StatusWebsiteGenerator()
    stats = {'known_peers':0, 'active_workers':1, 'available_assignments':0, 'global_highest_proven':0, 'average_rate': 0}
    cid = g.update_status(stats, None, 1, g.node_id)
    print('Status CID:', cid)
"""
PROJECT COLLATZ STATUS WEBSITE GENERATOR
=========================================
Generates decentralized status dashboard showing:
- Network health and progress
- Connected nodes and verification rate
- Link to leaderboard
- Current frontier (highest verified number)
- Real-time statistics

Fully decentralized: Any node can generate and publish to IPFS.
Content-addressing ensures consensus (identical data = same CID).
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Optional
import ipfshttpclient


class StatusWebsiteGenerator:
    """Generates ProjectCollatz status dashboard for IPFS."""
    
    def __init__(self, ipfs_api: str = '/ip4/127.0.0.1/tcp/5001'):
        """Initialize status website generator."""
        self.client = ipfshttpclient.connect(ipfs_api)
        self.node_id = self.client.id()['ID']
    
    def generate_status_html(self, network_stats: Dict, 
                            leaderboard_cid: Optional[str],
                            active_nodes: int,
                            node_id: str) -> str:
        """
        Generate HTML status dashboard.
        
        Args:
            network_stats: Network-wide statistics from coordinator
            leaderboard_cid: IPFS CID of current leaderboard
            active_nodes: Number of active nodes in network
            node_id: ID of this node
            
        Returns:
            HTML string
        """
        # Extract stats
        total_verified = network_stats.get('total_numbers_verified', 0)
        frontier = network_stats.get('highest_verified', 0)
        total_ranges = network_stats.get('total_assignments', 0)
        completed_ranges = network_stats.get('completed_assignments', 0)
        verification_rate = network_stats.get('network_rate_per_second', 0)
        
        # Calculate progress percentage (target: 2^68)
        target = 2 ** 68
        progress_percent = (frontier / target) * 100 if target > 0 else 0
        
        # Time estimate
        if verification_rate > 0:
            remaining = target - frontier
            seconds_remaining = remaining / verification_rate
            days_remaining = seconds_remaining / 86400
        else:
            days_remaining = float('inf')
        
        # Format numbers
        verified_formatted = f"{total_verified:,}"
        frontier_formatted = f"{frontier:,}"
        rate_formatted = f"{verification_rate:,.0f}"
        
        # Build HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="60">
    <title>ProjectCollatz - Decentralized Status Dashboard</title>
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
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        
        .header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .status-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.8;
            margin-bottom: 10px;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-unit {{
            font-size: 0.8em;
            opacity: 0.7;
        }}
        
        .progress-section {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        .progress-bar-container {{
            width: 100%;
            height: 40px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 20px;
            overflow: hidden;
            margin: 20px 0;
        }}
        
        .progress-bar {{
            height: 100%;
            background: linear-gradient(90deg, #00f260, #0575e6);
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }}
        
        .network-status {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
        }}
        
        .status-indicator {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #00ff00;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .links {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }}
        
        .btn {{
            padding: 15px 30px;
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 10px;
            color: #fff;
            text-decoration: none;
            font-weight: bold;
            transition: all 0.3s ease;
            display: inline-block;
        }}
        
        .btn:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.05);
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            opacity: 0.7;
            font-size: 0.9em;
        }}
        
        .info-box {{
            background: rgba(255, 255, 255, 0.05);
            border-left: 4px solid #00ff00;
            padding: 15px;
            border-radius: 5px;
            margin-top: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 ProjectCollatz</h1>
            <p class="subtitle">Decentralized Distributed Computing Network</p>
            <p class="subtitle">Proving the Collatz Conjecture - One Number at a Time</p>
        </div>
        
        <div class="progress-section">
            <h2>Global Progress</h2>
            <div class="network-status">
                <div class="status-indicator"></div>
                <span>Network Online - {active_nodes} Active Node{'s' if active_nodes != 1 else ''}</span>
            </div>
            
            <div class="progress-bar-container">
                <div class="progress-bar" style="width: {min(progress_percent, 100):.6f}%">
                    {progress_percent:.8f}%
                </div>
            </div>
            
            <div class="info-box">
                <strong>Current Frontier:</strong> {frontier_formatted}<br>
                <strong>Target:</strong> 2^68 ≈ 295,147,905,179,352,825,856<br>
                <strong>Progress:</strong> {completed_ranges}/{total_ranges} ranges completed
                {'<br><strong>Estimated Time:</strong> ' + f'{days_remaining:,.0f} days' if days_remaining != float('inf') else ''}
            </div>
        </div>
        
        <div class="status-grid">
            <div class="stat-card">
                <div class="stat-label">📊 Total Verified</div>
                <div class="stat-value">{verified_formatted}</div>
                <div class="stat-unit">numbers checked</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">⚡ Verification Rate</div>
                <div class="stat-value">{rate_formatted}</div>
                <div class="stat-unit">numbers/second</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">🌐 Active Nodes</div>
                <div class="stat-value">{active_nodes}</div>
                <div class="stat-unit">decentralized workers</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">✅ Completed Ranges</div>
                <div class="stat-value">{completed_ranges}</div>
                <div class="stat-unit">of {total_ranges} total</div>
            </div>
        </div>
        
        <div class="progress-section">
            <h2>🏆 Leaderboard & Links</h2>
            <div class="links">
                {f'<a href="https://ipfs.io/ipfs/{leaderboard_cid}" class="btn btn-primary">🏆 View Leaderboard</a>' if leaderboard_cid else '<p style="opacity: 0.7;">Leaderboard generating...</p>'}
                <a href="https://github.com/jaylouisw/projectcollatz" class="btn">📦 GitHub Repository</a>
                <a href="https://ipfs.io" class="btn">🌐 About IPFS</a>
            </div>
            
            <div class="info-box" style="margin-top: 20px;">
                <strong>🔐 Fully Decentralized:</strong> This network has no central server. 
                All nodes are equal peers, and the network runs forever with n>0 nodes!<br><br>
                <strong>🛡️ Byzantine Fault Tolerant:</strong> Multiple independent verifications 
                prevent fraud and ensure integrity.<br><br>
                <strong>🚀 Join the Network:</strong> Download the client and start contributing 
                your computing power to solve one of mathematics' most famous unsolved problems!
            </div>
        </div>
        
        <div class="footer">
            <p>Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            <p>Node ID: {node_id[:16]}...</p>
            <p>Auto-refreshes every 60 seconds</p>
            <p style="margin-top: 10px;">
                <small>This page is hosted on IPFS - Content-addressed and immutable</small>
            </p>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def publish_status(self, html: str) -> str:
        """
        Publish status website to IPFS.
        Returns IPFS CID.
        """
        cid = self.client.add_str(html)
        return cid
    
    def update_status(self, network_stats: Dict,
                     leaderboard_cid: Optional[str],
                     active_nodes: int,
                     node_id: str) -> Optional[str]:
        """
        Generate and publish status website.
        
        Args:
            network_stats: Network statistics from coordinator
            leaderboard_cid: Current leaderboard IPFS CID
            active_nodes: Number of active nodes
            node_id: This node's ID
            
        Returns:
            IPFS CID of published status page
        """
        try:
            # Generate HTML
            html = self.generate_status_html(
                network_stats, 
                leaderboard_cid,
                active_nodes,
                node_id
            )
            
            # Publish to IPFS
            cid = self.publish_status(html)
            
            return cid
            
        except Exception as e:
            print(f"[STATUS] Error updating: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    """Generate and publish status website."""
    from ipfs_coordinator import IPFSCoordinator
    
    # Initialize
    coordinator = IPFSCoordinator()
    generator = StatusWebsiteGenerator()
    
    # Get network stats
    network_stats = coordinator.get_network_statistics()
    active_nodes = len(coordinator.known_peers) + 1
    
    # Generate and publish
    cid = generator.update_status(
        network_stats=network_stats,
        leaderboard_cid=coordinator.canonical_leaderboard_cid,
        active_nodes=active_nodes,
        node_id=coordinator.node_id
    )
    
    if cid:
        print(f"\n{'='*60}")
        print(f"✅ ProjectCollatz Status Website Published!")
        print(f"{'='*60}")
        print(f"IPFS CID: {cid}")
        print(f"View at: https://ipfs.io/ipfs/{cid}")
        print(f"{'='*60}\n")
