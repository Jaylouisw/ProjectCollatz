#!/bin/bash
# ProjectCollatz Auto-Update Script for Raspberry Pi / SBC
# Place in /opt/projectcollatz/update.sh

set -e

LOG_FILE="/var/log/projectcollatz-update.log"
INSTALL_DIR="/opt/projectcollatz"
UPDATE_BRANCH="master"

echo "[$(date)] Starting update check..." >> "$LOG_FILE"

cd "$INSTALL_DIR"

# Check if git repository
if [ ! -d ".git" ]; then
    echo "[$(date)] ERROR: Not a git repository" >> "$LOG_FILE"
    exit 0
fi

# Fetch latest changes
git fetch origin "$UPDATE_BRANCH" >> "$LOG_FILE" 2>&1

# Check for updates
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/$UPDATE_BRANCH)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[$(date)] Update available, pulling changes..." >> "$LOG_FILE"
    
    # Stash any local changes
    git stash >> "$LOG_FILE" 2>&1 || true
    
    # Pull latest code
    git pull origin "$UPDATE_BRANCH" >> "$LOG_FILE" 2>&1
    
    # Update Python dependencies if changed
    if git diff-tree --no-commit-id --name-only -r HEAD | grep -q "requirements"; then
        echo "[$(date)] Updating Python dependencies..." >> "$LOG_FILE"
        source venv/bin/activate
        pip install --no-cache-dir -r requirements_distributed.txt >> "$LOG_FILE" 2>&1
    fi
    
    echo "[$(date)] ✓ Update complete" >> "$LOG_FILE"
else
    echo "[$(date)] Already up to date" >> "$LOG_FILE"
fi
