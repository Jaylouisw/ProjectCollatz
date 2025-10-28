# Installation Guide

Complete installation guide for all platforms and deployment scenarios.

## 🚀 Quick Install (Recommended)

### One-Command Installation

**Windows (PowerShell as Administrator):**
```powershell
iwr -useb https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.ps1 | iex
```

**Linux/macOS:**
```bash
curl -sSL https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.sh | bash
```

**Docker:**
```bash
docker pull jaylouisw/collatz-network:latest
docker run -it jaylouisw/collatz-network
```

### What the Install Scripts Do

1. **System Detection**: Identifies OS, architecture, and Python version
2. **Dependency Installation**: Installs Python, IPFS, and required packages
3. **Project Setup**: Downloads latest release and sets up directories
4. **Configuration**: Creates initial configuration files
5. **Testing**: Verifies installation with compatibility checks
6. **Start Options**: Provides multiple ways to launch the system

---

## 📋 System Requirements

### Minimum Requirements
- **Python**: 3.8 or newer
- **RAM**: 2GB minimum (4GB+ recommended)
- **Disk**: 500MB for software, minimal for data
- **Network**: Internet connection for distributed mode
- **OS**: Windows 10+, Linux (Ubuntu 20.04+), macOS 11+

### Recommended Requirements
- **Python**: 3.10 or newer
- **RAM**: 8GB+ for optimal performance
- **CPU**: 4+ cores for parallel processing
- **GPU**: NVIDIA CUDA or AMD ROCm for acceleration
- **Network**: Stable broadband connection

### Optional Components
- **NVIDIA GPU**: 10x-100x performance boost with CUDA
- **AMD GPU**: Performance boost with ROCm (Linux)
- **Docker**: For containerized deployment
- **Git**: For development and manual installation

---

## 🖥️ Platform-Specific Installation

### Windows Installation

#### Method 1: Automated Script (Recommended)
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
iwr -useb https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.ps1 | iex
```

#### Method 2: Manual Installation
```powershell
# Install Python 3.10+
winget install Python.Python.3.11

# Install Git
winget install Git.Git

# Clone repository
git clone https://github.com/Jaylouisw/ProjectCollatz.git
cd ProjectCollatz

# Install dependencies
pip install -r requirements_distributed.txt

# Install IPFS
# Download from: https://docs.ipfs.tech/install/
# Extract to C:\Program Files\IPFS and add to PATH

# Initialize IPFS
ipfs init

# Test installation
python future_proof_engine.py --test
```

#### Windows-Specific Notes
- **PowerShell**: Use PowerShell 5.1+ or PowerShell Core 7+
- **Execution Policy**: May need to allow script execution
- **Windows Defender**: May flag cryptocurrency-related processes (false positive)
- **WSL**: Full Linux compatibility available via Windows Subsystem for Linux

### Linux Installation

#### Method 1: Automated Script (Recommended)
```bash
curl -sSL https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.sh | bash
```

#### Method 2: Manual Installation

**Ubuntu/Debian:**
```bash
# Update package list
sudo apt update

# Install Python and development tools
sudo apt install python3 python3-pip python3-venv git curl

# Install IPFS
wget https://dist.ipfs.tech/kubo/v0.22.0/kubo_v0.22.0_linux-amd64.tar.gz
tar -xvzf kubo_v0.22.0_linux-amd64.tar.gz
cd kubo
sudo bash install.sh
cd ..

# Clone repository
git clone https://github.com/Jaylouisw/ProjectCollatz.git
cd ProjectCollatz

# Create virtual environment (recommended)
python3 -m venv collatz-env
source collatz-env/bin/activate

# Install dependencies
pip install -r requirements_distributed.txt

# Initialize IPFS
ipfs init

# Test installation
python future_proof_engine.py --test
```

**Red Hat/CentOS/Fedora:**
```bash
# Install Python and development tools
sudo dnf install python3 python3-pip python3-devel git curl

# Continue with Ubuntu instructions above
```

**Arch Linux:**
```bash  
# Install Python and development tools
sudo pacman -S python python-pip git curl

# Install IPFS from AUR
yay -S kubo-bin

# Continue with Ubuntu instructions above
```

### macOS Installation

#### Method 1: Automated Script (Recommended)
```bash
curl -sSL https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.sh | bash
```

#### Method 2: Homebrew Installation
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 git ipfs

# Clone repository
git clone https://github.com/Jaylouisw/ProjectCollatz.git
cd ProjectCollatz

# Install Python dependencies
pip3 install -r requirements_distributed.txt

# Initialize IPFS
ipfs init

# Test installation
python3 future_proof_engine.py --test
```

#### Method 3: Manual Installation
```bash
# Install Python from python.org
# Download from: https://www.python.org/downloads/macos/

# Install Git (included with Xcode Command Line Tools)
xcode-select --install

# Install IPFS
curl -O https://dist.ipfs.tech/kubo/v0.22.0/kubo_v0.22.0_darwin-amd64.tar.gz
tar -xvzf kubo_v0.22.0_darwin-amd64.tar.gz
cd kubo
sudo bash install.sh
cd ..

# Continue with Linux instructions above
```

---

## 🐳 Container Deployment

### Docker Installation

#### Quick Start
```bash
# Pull and run latest image
docker pull jaylouisw/collatz-network:latest
docker run -it --name collatz-worker jaylouisw/collatz-network
```

#### Persistent Data
```bash
# Run with persistent configuration and keys
docker run -it \
  --name collatz-worker \
  -v ./collatz-data:/app/data \
  -v ./collatz-keys:/app/keys \
  jaylouisw/collatz-network
```

#### Background Service
```bash
# Run as background service
docker run -d \
  --name collatz-worker \
  --restart unless-stopped \
  -v ./collatz-data:/app/data \
  jaylouisw/collatz-network \
  python future_proof_engine.py
```

### Docker Compose Deployment

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  collatz-worker:
    image: jaylouisw/collatz-network:latest
    container_name: collatz-worker
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./keys:/app/keys
      - ./config:/app/config
    environment:
      - COLLATZ_WORKER_NAME=docker-worker-01
      - COLLATZ_LOG_LEVEL=INFO
    command: python future_proof_engine.py

  # Multiple workers
  collatz-worker-2:
    image: jaylouisw/collatz-network:latest
    container_name: collatz-worker-2
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./keys:/app/keys
    environment:
      - COLLATZ_WORKER_NAME=docker-worker-02
    command: python future_proof_engine.py
```

**Start services:**
```bash
docker-compose up -d
```

### Kubernetes Deployment

**collatz-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: collatz-workers
spec:
  replicas: 3
  selector:
    matchLabels:
      app: collatz-worker
  template:
    metadata:
      labels:
        app: collatz-worker
    spec:
      containers:
      - name: collatz-worker
        image: jaylouisw/collatz-network:latest
        command: ["python", "future_proof_engine.py"]
        env:
        - name: COLLATZ_LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        volumeMounts:
        - name: config
          mountPath: /app/config
        - name: data
          mountPath: /app/data
      volumes:
      - name: config
        configMap:
          name: collatz-config
      - name: data
        emptyDir: {}
```

**Deploy to Kubernetes:**
```bash
kubectl apply -f collatz-deployment.yaml
```

---

## 🍓 Single Board Computer Installation

### Raspberry Pi

#### Pre-built Images (Recommended)
1. **Download**: Get the latest image from [Releases](https://github.com/Jaylouisw/ProjectCollatz/releases)
2. **Flash**: Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) or [Balena Etcher](https://www.balena.io/etcher/)
3. **Boot**: Insert SD card and power on
4. **Setup**: System auto-configures on first boot (5-10 minutes)
5. **Connect**: SSH to `pi@raspberrypi.local` (password: `collatz`)
6. **Start**: Run `cd collatz-network && python3 future_proof_engine.py`

#### Manual Installation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3 python3-pip python3-venv git curl -y

# Install IPFS (ARM64)
wget https://dist.ipfs.tech/kubo/v0.22.0/kubo_v0.22.0_linux-arm64.tar.gz
tar -xvzf kubo_v0.22.0_linux-arm64.tar.gz
cd kubo
sudo bash install.sh
cd ..

# Clone and setup
git clone https://github.com/Jaylouisw/ProjectCollatz.git
cd ProjectCollatz
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_distributed.txt

# Initialize and test
ipfs init
python3 future_proof_engine.py --test
```

### Other ARM Boards

**Orange Pi / Rock Pi / Odroid:**
- Use Linux ARM64/ARM32 installation instructions
- Ensure adequate cooling for sustained computation
- Consider power supply requirements for GPU-enabled boards

**Installation variations:**
```bash
# For 32-bit ARM systems
wget https://dist.ipfs.tech/kubo/v0.22.0/kubo_v0.22.0_linux-arm.tar.gz

# For 64-bit ARM systems  
wget https://dist.ipfs.tech/kubo/v0.22.0/kubo_v0.22.0_linux-arm64.tar.gz
```

---

## ☁️ Cloud Deployment

### AWS Deployment

#### EC2 Instance
```bash
# Launch Ubuntu 22.04 LTS instance (t3.medium or larger)
# SSH into instance

# Run automated installation
curl -sSL https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.sh | bash

# Start as service
sudo systemctl enable collatz-worker
sudo systemctl start collatz-worker
```

#### ECS/Fargate
```json
{
  "family": "collatz-worker",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "collatz-worker",
      "image": "jaylouisw/collatz-network:latest",
      "command": ["python", "future_proof_engine.py"],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/collatz-worker",
          "awslogs-region": "us-east-1"
        }
      }
    }
  ]
}
```

### Google Cloud Deployment

#### Compute Engine
```bash
# Create instance
gcloud compute instances create collatz-worker \
  --image-family ubuntu-2204-lts \
  --image-project ubuntu-os-cloud \
  --machine-type e2-standard-2 \
  --zone us-central1-a

# SSH and install
gcloud compute ssh collatz-worker
curl -sSL https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.sh | bash
```

#### Google Kubernetes Engine
```bash
# Create cluster
gcloud container clusters create collatz-cluster --num-nodes=3

# Deploy application
kubectl apply -f k8s/collatz-deployment.yaml
```

### Azure Deployment

#### Virtual Machine
```bash
# Create VM
az vm create \
  --resource-group myResourceGroup \
  --name collatz-worker \
  --image Ubuntu2204 \
  --size Standard_B2s \
  --generate-ssh-keys

# SSH and install
ssh azureuser@<public-ip>
curl -sSL https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.sh | bash
```

#### Azure Container Instances
```bash
az container create \
  --resource-group myResourceGroup \
  --name collatz-worker \
  --image jaylouisw/collatz-network:latest \
  --cpu 2 \
  --memory 4 \
  --restart-policy Always
```

---

## 🔧 GPU Support Installation

### NVIDIA CUDA Setup

#### Linux CUDA Installation
```bash
# Install NVIDIA drivers
sudo apt install nvidia-driver-525

# Install CUDA toolkit
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt update
sudo apt install cuda-toolkit-12-2

# Install cuDNN (optional, for enhanced performance)
# Download from NVIDIA Developer website
sudo dpkg -i cudnn-local-repo-ubuntu2204-8.9.2.26_1.0-1_amd64.deb
sudo cp /var/cudnn-local-repo-ubuntu2204-8.9.2.26/cudnn-local-08A7D361-keyring.gpg /usr/share/keyrings/
sudo apt update
sudo apt install libcudnn8

# Verify installation
nvidia-smi
nvcc --version
```

#### Windows CUDA Installation
1. **Download**: [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads) from NVIDIA
2. **Install**: Run installer with default options
3. **Verify**: Open Command Prompt and run `nvidia-smi`
4. **Test**: Run `python future_proof_engine.py --test` to verify GPU detection

### AMD ROCm Setup (Linux only)

```bash
# Add ROCm repository
wget -q -O - https://repo.radeon.com/rocm/rocm.gpg.key | sudo apt-key add -
echo 'deb [arch=amd64] https://repo.radeon.com/rocm/apt/5.4.3 ubuntu main' | sudo tee /etc/apt/sources.list.d/rocm.list

# Install ROCm
sudo apt update
sudo apt install rocm-dkms rocm-libs

# Add user to render group
sudo usermod -a -G render $USER

# Reboot required
sudo reboot

# Verify installation
rocm-smi
```

---

## ⚙️ Configuration

### Initial Configuration

After installation, the system creates a default configuration file:

**collatz_config.json:**
```json
{
  "version": "2.0",
  "network": {
    "transport": "auto",
    "ipfs_api": "/ip4/127.0.0.1/tcp/5001",
    "connection_timeout": 30,
    "retry_count": 3
  },
  "compute": {
    "engine": "auto",
    "max_workers": 0,
    "prefer_gpu": true,
    "cpu_threads": 0
  },
  "security": {
    "verification_required": true,
    "trust_threshold": 100,
    "max_verification_time": 300
  },
  "deployment": {
    "worker_name": "auto",
    "log_level": "INFO",
    "metrics_enabled": true
  }
}
```

### Environment Variables

Override configuration with environment variables:

```bash
# Network settings
export COLLATZ_NETWORK_TRANSPORT=ipfs
export COLLATZ_IPFS_API=/ip4/127.0.0.1/tcp/5001

# Compute settings  
export COLLATZ_COMPUTE_ENGINE=cuda
export COLLATZ_MAX_WORKERS=8
export COLLATZ_PREFER_GPU=true

# Deployment settings
export COLLATZ_WORKER_NAME=production-node-01
export COLLATZ_LOG_LEVEL=DEBUG
```

### Advanced Configuration

**GPU-Specific Settings:**
```json
{
  "compute": {
    "cuda": {
      "device_id": 0,
      "memory_fraction": 0.8,
      "allow_growth": true
    },
    "rocm": {
      "device_id": 0,
      "memory_pool_size": "4GB"
    }
  }
}
```

**Network Tuning:**
```json
{
  "network": {
    "ipfs": {
      "swarm_addresses": [
        "/ip4/0.0.0.0/tcp/4001",
        "/ip6/::/tcp/4001"
      ],
      "bootstrap_peers": "default",
      "connection_manager": {
        "low_water": 50,
        "high_water": 200
      }
    }
  }
}
```

---

## ✅ Verification & Testing

### System Compatibility Check

```bash
# Check system compatibility
python future_proof_engine.py --info

# Expected output:
# System Information:
#   Platform: Linux Ubuntu
#   Architecture: x86_64
#   Python: 3.10.12
# 
# Component Availability:
#   Network Transport: ✓ (IPFSTransport)
#   Compute Engine: ✓ (CUDAComputeEngine)
#   Configuration Manager: ✓
#   Available Transports: ipfs
#   Available Engines: cpu, cuda
```

### Functionality Test

```bash
# Run comprehensive test
python future_proof_engine.py --test

# Expected output:
# Running basic functionality test...
# ✓ Configuration loaded: CollatzConfig
# Testing compute verification...
# ✓ Verified range 1-100 in 0.003s using CUDA
# ✓ Network transport available
# 
# Basic functionality test completed!
```

### Network Connectivity Test

```bash
# Test IPFS connectivity
ipfs swarm peers

# Should show connected peers
# /ip4/104.131.131.82/tcp/4001/p12D3KooW...
# /ip4/104.236.176.52/tcp/4001/p12D3KooW...
```

### Performance Benchmark

```bash
# Run performance benchmark
python benchmark.py

# Expected output shows verification rates:
# CPU Performance: 1.2M numbers/second
# GPU Performance: 8.5B numbers/second  
# Network Latency: 15ms average
```

---

## 🔄 Starting the System

### Option 1: Future-Proof Engine (Recommended)

```bash
# Start with automatic configuration
python future_proof_engine.py

# Start in local mode (offline)
python future_proof_engine.py --local

# Custom configuration
python future_proof_engine.py --config my_config.json
```

### Option 2: Interactive Launcher

```bash
# Start interactive menu
python network_launcher.py

# Follow menu prompts:
# 1. Start Worker (with account)
# 2. Start Worker (anonymous)  
# 3. Start Worker (CPU-only)
# 4. Create User Account
```

### Option 3: Direct Worker Mode

```bash
# Create user account first
python -c "from user_account import UserAccountManager; UserAccountManager().create_account('myusername')"

# Start worker
python distributed_collatz.py --user-key ./keys/myusername_private_key.pem
```

### Starting as Service

#### Linux (systemd)

**Create service file:**
```bash
sudo tee /etc/systemd/system/collatz-worker.service > /dev/null <<EOF
[Unit]
Description=Collatz Distributed Worker
After=network.target

[Service]
Type=simple
User=collatz
WorkingDirectory=/home/collatz/ProjectCollatz
ExecStart=/usr/bin/python3 future_proof_engine.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable collatz-worker
sudo systemctl start collatz-worker

# Check status
sudo systemctl status collatz-worker
```

#### Windows (Service)

```powershell
# Install as Windows service using NSSM
# Download NSSM from: https://nssm.cc/download

nssm install CollatzWorker
nssm set CollatzWorker Application "C:\Python311\python.exe"
nssm set CollatzWorker AppParameters "future_proof_engine.py"
nssm set CollatzWorker AppDirectory "C:\Users\%USERNAME%\ProjectCollatz"
nssm set CollatzWorker Description "Collatz Distributed Worker"

# Start service
sc start CollatzWorker
```

---

## 🐛 Troubleshooting

### Common Issues

#### Python Version Issues
```bash
# Error: Python 3.8+ required
# Solution: Install newer Python version

# Check current version
python --version

# Install Python 3.11 (recommended)
# Windows: winget install Python.Python.3.11
# Ubuntu: sudo apt install python3.11 python3.11-pip
# macOS: brew install python@3.11
```

#### IPFS Connection Issues
```bash
# Error: IPFS daemon not running
# Solution: Start IPFS daemon

# Initialize IPFS (first time only)
ipfs init

# Start daemon
ipfs daemon

# Check status
ipfs swarm peers
```

#### GPU Detection Issues
```bash
# Error: CUDA/ROCm not detected
# Solution: Install GPU drivers and toolkit

# NVIDIA: Check nvidia-smi output
nvidia-smi

# AMD: Check rocm-smi output  
rocm-smi

# Verify in Python
python -c "import torch; print(torch.cuda.is_available())"
```

#### Permission Issues (Linux)
```bash
# Error: Permission denied
# Solution: Check file permissions and user groups

# Fix file permissions
chmod +x install.sh
chmod +x *.py

# Add user to docker group (if using Docker)
sudo usermod -a -G docker $USER

# Add user to render group (for GPU access)
sudo usermod -a -G render $USER
```

#### Network Firewall Issues
```bash
# Error: Cannot connect to IPFS network
# Solution: Configure firewall

# Open IPFS ports
sudo ufw allow 4001  # IPFS swarm
sudo ufw allow 5001  # IPFS API
sudo ufw allow 8080  # IPFS gateway

# Windows Firewall
# Allow Python.exe through Windows Defender Firewall
```

### Getting Help

1. **Check Logs**: Look for error messages in console output
2. **Run Diagnostics**: `python run_diagnostics.py`
3. **Test Components**: `python future_proof_engine.py --test`
4. **Check GitHub Issues**: [Open Issues](https://github.com/Jaylouisw/ProjectCollatz/issues)
5. **Create Issue**: Report problems with system info and logs

### Debug Mode

```bash
# Enable debug logging
export COLLATZ_LOG_LEVEL=DEBUG
python future_proof_engine.py

# Or via config file
{
  "deployment": {
    "log_level": "DEBUG"
  }
}
```

---

## 📈 Next Steps

After successful installation:

1. **Join the Network**: Start contributing to the global verification effort
2. **Create Account**: Get recognition for your contributions
3. **Monitor Progress**: Check your statistics and the global leaderboard  
4. **Optimize Performance**: Tune settings for your hardware
5. **Scale Up**: Add more workers or upgrade hardware
6. **Contribute**: Help improve the project with code or documentation

**Welcome to the Collatz Distributed Network!** 🎉