#!/bin/bash
# ProjectCollatz One-Command Linux/Mac Installer
# Usage: curl -sSL https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/quick-install.sh | bash

set -e  # Exit on error

echo "==================================="
echo "   ProjectCollatz Installer"
echo "==================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Step 1: Check Python
echo -e "${YELLOW}[1/6] Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
        echo -e "${GREEN}  ✓ Python 3.8+ found: $PYTHON_VERSION${NC}"
    else
        echo -e "${RED}  ✗ Python 3.8+ required. Found: $PYTHON_VERSION${NC}"
        echo -e "${YELLOW}  → Install Python 3.8+${NC}"
        exit 1
    fi
else
    echo -e "${RED}  ✗ Python 3 not found${NC}"
    echo -e "${YELLOW}  → Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip${NC}"
    echo -e "${YELLOW}  → Fedora/RHEL:   sudo dnf install python3 python3-pip${NC}"
    echo -e "${YELLOW}  → macOS:         brew install python3${NC}"
    exit 1
fi

# Step 2: Create virtual environment
echo -e "${YELLOW}[2/6] Creating Python virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${CYAN}  ℹ Virtual environment already exists, skipping...${NC}"
else
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}  ✓ Virtual environment created${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Step 3: Install Python dependencies
echo -e "${YELLOW}[3/6] Installing Python dependencies...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null
if [ -f "requirements_distributed.txt" ]; then
    pip install -r requirements_distributed.txt
    echo -e "${GREEN}  ✓ Python packages installed${NC}"
else
    echo -e "${RED}  ✗ requirements_distributed.txt not found${NC}"
    echo -e "${YELLOW}  → Make sure you're in the ProjectCollatz directory${NC}"
    exit 1
fi

# Step 4: Check/Install IPFS
echo -e "${YELLOW}[4/6] Checking IPFS installation...${NC}"
if command -v ipfs &> /dev/null; then
    IPFS_VERSION=$(ipfs version | head -n1)
    echo -e "${GREEN}  ✓ IPFS found: $IPFS_VERSION${NC}"
else
    echo -e "${CYAN}  ℹ IPFS not found, installing...${NC}"
    
    # Detect OS
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    
    # Map architecture names
    case $ARCH in
        x86_64) ARCH="amd64" ;;
        aarch64|arm64) ARCH="arm64" ;;
        armv7l) ARCH="arm" ;;
        *) echo -e "${RED}  ✗ Unsupported architecture: $ARCH${NC}"; exit 1 ;;
    esac
    
    # Map OS names
    case $OS in
        linux) OS="linux" ;;
        darwin) OS="darwin" ;;
        *) echo -e "${RED}  ✗ Unsupported OS: $OS${NC}"; exit 1 ;;
    esac
    
    IPFS_VERSION="v0.31.0"
    IPFS_FILE="kubo_${IPFS_VERSION}_${OS}-${ARCH}.tar.gz"
    IPFS_URL="https://dist.ipfs.tech/kubo/$IPFS_VERSION/$IPFS_FILE"
    
    echo -e "${CYAN}  → Downloading IPFS...${NC}"
    curl -sSL -o /tmp/ipfs.tar.gz "$IPFS_URL"
    
    echo -e "${CYAN}  → Extracting...${NC}"
    tar -xzf /tmp/ipfs.tar.gz -C /tmp
    
    # Try to install system-wide (if sudo available)
    if command -v sudo &> /dev/null; then
        echo -e "${CYAN}  → Installing to /usr/local/bin (requires sudo)...${NC}"
        sudo mv /tmp/kubo/ipfs /usr/local/bin/ipfs
        sudo chmod +x /usr/local/bin/ipfs
    else
        # Install to user directory
        echo -e "${CYAN}  → Installing to ~/.local/bin...${NC}"
        mkdir -p ~/.local/bin
        mv /tmp/kubo/ipfs ~/.local/bin/ipfs
        chmod +x ~/.local/bin/ipfs
        
        # Add to PATH if not already
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
            echo -e "${YELLOW}  ⚠ Added ~/.local/bin to PATH in ~/.bashrc${NC}"
            echo -e "${YELLOW}  → Run: source ~/.bashrc${NC}"
            export PATH="$HOME/.local/bin:$PATH"
        fi
    fi
    
    rm -rf /tmp/kubo /tmp/ipfs.tar.gz
    echo -e "${GREEN}  ✓ IPFS installed${NC}"
fi

# Step 5: Initialize IPFS
echo -e "${YELLOW}[5/6] Initializing IPFS repository...${NC}"
if [ -d "$HOME/.ipfs" ]; then
    echo -e "${CYAN}  ℹ IPFS already initialized${NC}"
else
    ipfs init
    echo -e "${GREEN}  ✓ IPFS initialized${NC}"
fi

# Step 6: Start IPFS daemon
echo -e "${YELLOW}[6/6] Starting IPFS daemon...${NC}"
if pgrep -x "ipfs" > /dev/null; then
    echo -e "${CYAN}  ℹ IPFS daemon already running${NC}"
else
    nohup ipfs daemon > ipfs_daemon.log 2>&1 &
    sleep 3
    
    if pgrep -x "ipfs" > /dev/null; then
        echo -e "${GREEN}  ✓ IPFS daemon started (logs: ipfs_daemon.log)${NC}"
    else
        echo -e "${YELLOW}  ⚠ IPFS daemon may not have started, check ipfs_daemon.log${NC}"
    fi
fi

echo ""
echo -e "${GREEN}===================================${NC}"
echo -e "${GREEN}   Installation Complete!${NC}"
echo -e "${GREEN}===================================${NC}"
echo ""
echo -e "${CYAN}Quick Start:${NC}"
echo -e "  1. Activate environment: ${WHITE}source venv/bin/activate${NC}"
echo -e "  2. Run worker:          ${WHITE}python distributed_collatz.py${NC}"
echo -e "  3. Check status:        ${WHITE}python distributed_collatz.py --status${NC}"
echo ""
echo -e "${CYAN}Documentation:${NC}"
echo -e "  README.md        - Project overview"
echo -e "  USER_GUIDE.md    - Detailed usage guide"
echo -e "  SECURITY.md      - Security architecture"
echo ""
echo -e "${CYAN}Support: https://github.com/Jaylouisw/ProjectCollatz/issues${NC}"
echo ""
