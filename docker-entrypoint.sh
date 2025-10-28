#!/bin/bash
# ProjectCollatz Docker Entry Point with Auto-Update
set -e

echo "====================================="
echo "  ProjectCollatz Distributed Worker"
echo "====================================="
echo ""

# Function to check for updates
check_and_update() {
    if [ "$AUTO_UPDATE" != "true" ]; then
        echo "[UPDATE] Auto-update disabled"
        return 0
    fi
    
    echo "[UPDATE] Checking for updates from GitHub..."
    cd /app
    
    # Initialize git if not already (for mounted volumes)
    if [ ! -d ".git" ]; then
        echo "[UPDATE] Not a git repository, skipping update"
        return 0
    fi
    
    # Fetch latest changes
    git fetch origin $UPDATE_BRANCH
    
    # Check if updates available
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/$UPDATE_BRANCH)
    
    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "[UPDATE] New version available, updating..."
        
        # Stash any local changes
        git stash
        
        # Pull latest code
        git pull origin $UPDATE_BRANCH
        
        # Update Python dependencies if requirements changed
        if git diff-tree --no-commit-id --name-only -r HEAD | grep -q "requirements"; then
            echo "[UPDATE] Requirements changed, updating packages..."
            pip install --no-cache-dir -r requirements_distributed.txt
        fi
        
        echo "[UPDATE] ✓ Update complete"
    else
        echo "[UPDATE] Already up to date"
    fi
}

# Check for updates on startup
check_and_update

# Start IPFS daemon in background
echo "[IPFS] Starting daemon..."
ipfs daemon &
IPFS_PID=$!

# Wait for IPFS to be ready
sleep 3

# Trap signals to gracefully shutdown
trap 'echo "[SHUTDOWN] Stopping services..."; kill $IPFS_PID 2>/dev/null; exit 0' SIGTERM SIGINT

# Execute the main command
exec "$@"
