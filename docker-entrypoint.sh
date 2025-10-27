#!/bin/bash
# Docker entrypoint script for Collatz Network

set -e

# Start IPFS daemon in background
echo "Starting IPFS daemon..."
ipfs daemon &
IPFS_PID=$!

# Wait for IPFS to be ready
sleep 3

# Trap SIGTERM and SIGINT to gracefully shutdown
trap "kill $IPFS_PID; exit 0" SIGTERM SIGINT

# Execute the main command
exec "$@"
