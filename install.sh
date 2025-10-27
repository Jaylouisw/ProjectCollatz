#!/bin/bash
# Collatz Distributed Network - Linux/macOS Installer
# Single-command installation script
# Usage: curl -sSL https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.sh | bash

set -e

echo "=========================================="
echo "  Collatz Distributed Network Installer"
echo "=========================================="
echo

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "Detected OS: $MACHINE"
echo

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed!"
    echo "Please install Python 3.8 or later and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $PYTHON_VERSION"

# Check if Python version is >= 3.8
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "ERROR: Python 3.8 or later is required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✓ Python version OK"
echo

# Create installation directory
INSTALL_DIR="$HOME/collatz-network"
echo "Installation directory: $INSTALL_DIR"

if [ -d "$INSTALL_DIR" ]; then
    echo "Directory already exists. Updating..."
else
    echo "Creating directory..."
    mkdir -p "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# Clone or update repository
if [ -d ".git" ]; then
    echo "Updating existing installation..."
    git pull
else
    echo "Cloning repository..."
    if [ -n "$(ls -A .)" ]; then
        echo "ERROR: Directory is not empty and not a git repository!"
        exit 1
    fi
    git clone https://github.com/Jaylouisw/ProjectCollatz.git .
fi

echo "✓ Repository cloned/updated"
echo

# Install Python dependencies
echo "Installing Python dependencies..."
python3 -m pip install --user --upgrade pip
python3 -m pip install --user -r requirements_distributed.txt

echo "✓ Python dependencies installed"
echo

# Check for GPU support (optional)
echo "Checking for GPU support..."
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected!"
    read -p "Install GPU support (CuPy)? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Detect CUDA version
        if command -v nvcc &> /dev/null; then
            CUDA_VERSION=$(nvcc --version | grep "release" | sed -n 's/.*release \([0-9]*\.[0-9]*\).*/\1/p')
            CUDA_MAJOR=$(echo $CUDA_VERSION | cut -d'.' -f1)
            echo "CUDA version detected: $CUDA_VERSION"
            
            if [ "$CUDA_MAJOR" -ge 12 ]; then
                echo "Installing CuPy for CUDA 12.x..."
                python3 -m pip install --user cupy-cuda12x==13.0.0
            else
                echo "Installing CuPy for CUDA 11.x..."
                python3 -m pip install --user cupy-cuda11x==13.0.0
            fi
            echo "✓ GPU support installed"
        else
            echo "WARNING: nvcc not found. Cannot determine CUDA version."
            echo "Please install CuPy manually: pip install cupy-cuda12x or cupy-cuda11x"
        fi
    fi
else
    echo "No NVIDIA GPU detected. Skipping GPU support."
    echo "(CPU-only mode will be used)"
fi
echo

# Install IPFS
echo "Checking for IPFS..."
if command -v ipfs &> /dev/null; then
    IPFS_VERSION=$(ipfs --version | cut -d' ' -f3)
    echo "✓ IPFS already installed (version $IPFS_VERSION)"
else
    echo "IPFS not found. Installing..."
    
    if [ "$MACHINE" = "Linux" ]; then
        # Linux installation
        IPFS_VERSION="v0.24.0"
        ARCH="$(uname -m)"
        
        if [ "$ARCH" = "x86_64" ]; then
            IPFS_ARCH="amd64"
        elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
            IPFS_ARCH="arm64"
        elif [[ "$ARCH" == arm* ]]; then
            IPFS_ARCH="arm"
        else
            echo "WARNING: Unsupported architecture: $ARCH"
            echo "Please install IPFS manually from: https://docs.ipfs.tech/install/"
            IPFS_ARCH=""
        fi
        
        if [ -n "$IPFS_ARCH" ]; then
            wget "https://dist.ipfs.tech/kubo/${IPFS_VERSION}/kubo_${IPFS_VERSION}_linux-${IPFS_ARCH}.tar.gz" -O /tmp/ipfs.tar.gz
            tar -xvzf /tmp/ipfs.tar.gz -C /tmp
            sudo mv /tmp/kubo/ipfs /usr/local/bin/ipfs
            rm -rf /tmp/ipfs.tar.gz /tmp/kubo
            echo "✓ IPFS installed"
        fi
        
    elif [ "$MACHINE" = "Mac" ]; then
        # macOS installation
        if command -v brew &> /dev/null; then
            brew install ipfs
            echo "✓ IPFS installed via Homebrew"
        else
            echo "Homebrew not found. Please install IPFS manually:"
            echo "https://docs.ipfs.tech/install/"
        fi
    fi
fi

# Initialize IPFS if needed
if [ ! -d "$HOME/.ipfs" ]; then
    echo "Initializing IPFS..."
    ipfs init
    echo "✓ IPFS initialized"
else
    echo "✓ IPFS already initialized"
fi

echo

# Create launch script
echo "Creating launch script..."
cat > "$INSTALL_DIR/start.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"

# Start IPFS daemon in background if not running
if ! pgrep -x "ipfs" > /dev/null; then
    echo "Starting IPFS daemon..."
    ipfs daemon &
    sleep 3
fi

# Start the launcher
python3 network_launcher.py
EOF

chmod +x "$INSTALL_DIR/start.sh"

echo "✓ Launch script created"
echo

# Installation complete
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo
echo "To start the Collatz Network:"
echo "  cd $INSTALL_DIR"
echo "  ./start.sh"
echo
echo "Or add to your shell profile for easier access:"
echo "  alias collatz='cd $INSTALL_DIR && ./start.sh'"
echo
echo "Documentation:"
echo "  README.md - Project overview"
echo "  DISTRIBUTED_QUICKREF.md - Quick reference"
echo "  DISTRIBUTED.md - Complete documentation"
echo
