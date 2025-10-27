#!/bin/bash
# Collatz Network - Multi-Platform SBC Image Builder
# Creates OS images with Collatz Network pre-installed for various Single Board Computers
# Supports: Raspberry Pi (all models), Orange Pi, Rock Pi, Odroid, and other ARM SBCs

set -e

# Configuration arrays for different platforms
# Note: Raspberry Pi 3 has 64-bit ARM CPU but ships with 32-bit OS by default
# We provide both options: rpi3-arm64 (better performance) and rpi3-arm32 (compatibility)
declare -A PLATFORMS=(
    ["rpi4-arm64"]="2024-03-15-raspios-bookworm-arm64-lite"
    ["rpi4-arm32"]="2024-03-15-raspios-bookworm-armhf-lite"
    ["rpi3-arm64"]="2024-03-15-raspios-bookworm-arm64-lite"      # Pi 3 with 64-bit OS
    ["rpi3-arm32"]="2024-03-15-raspios-bookworm-armhf-lite"      # Pi 3 with 32-bit OS
    ["rpi-zero2"]="2024-03-15-raspios-bookworm-arm64-lite"
    ["rpi-legacy"]="2024-03-15-raspios-bookworm-armhf-lite"      # Pi 1, 2, Zero (32-bit only)
    ["ubuntu-arm64"]="ubuntu-22.04.3-preinstalled-server-arm64+raspi"
    ["ubuntu-arm32"]="ubuntu-22.04.3-preinstalled-server-armhf+raspi"
)

declare -A DOWNLOAD_URLS=(
    ["rpi4-arm64"]="https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2024-03-15/"
    ["rpi4-arm32"]="https://downloads.raspberrypi.com/raspios_lite_armhf/images/raspios_lite_armhf-2024-03-15/"
    ["rpi3-arm64"]="https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2024-03-15/"
    ["rpi3-arm32"]="https://downloads.raspberrypi.com/raspios_lite_armhf/images/raspios_lite_armhf-2024-03-15/"
    ["rpi-zero2"]="https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2024-03-15/"
    ["rpi-legacy"]="https://downloads.raspberrypi.com/raspios_lite_armhf/images/raspios_lite_armhf-2024-03-15/"
    ["ubuntu-arm64"]="https://cdimage.ubuntu.com/ubuntu-server/releases/22.04/release/"
    ["ubuntu-arm32"]="https://cdimage.ubuntu.com/ubuntu-server/releases/22.04/release/"
)

# Default configuration
DEFAULT_PLATFORM="rpi4-arm64"
WORK_DIR="./pi-build"
DATE_STAMP=$(date +%Y%m%d)

# Parse command line arguments
PLATFORM="$DEFAULT_PLATFORM"
BUILD_ALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --platform=*)
            PLATFORM="${1#*=}"
            shift
            ;;
        --all)
            BUILD_ALL=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--platform=PLATFORM] [--all] [--help]"
            echo ""
            echo "Available platforms:"
            echo "  rpi4-arm64    - Raspberry Pi 4, 400, CM4 (64-bit)"
            echo "  rpi4-arm32    - Raspberry Pi 4, 400, CM4 (32-bit)"  
            echo "  rpi3-arm64    - Raspberry Pi 3, 3B+ (64-bit)"
            echo "  rpi3-arm32    - Raspberry Pi 3, 3B+ (32-bit)"
            echo "  rpi-zero2     - Raspberry Pi Zero 2 W (64-bit)"
            echo "  rpi-legacy    - Raspberry Pi 1, 2, Zero (32-bit)"
            echo "  ubuntu-arm64  - Orange Pi, Rock Pi, Odroid (64-bit)"
            echo "  ubuntu-arm32  - Older ARM32 SBCs"
            echo ""
            echo "Options:"
            echo "  --platform=PLATFORM  Build for specific platform (default: $DEFAULT_PLATFORM)"
            echo "  --all                Build for all supported platforms"
            echo "  --help               Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "  Collatz Network - Multi-Platform Builder"
echo "=========================================="
echo

# Check if running on Linux
if [ "$(uname -s)" != "Linux" ]; then
    echo "ERROR: This script must run on Linux (or in Docker)"
    exit 1
fi

# Check for required tools
REQUIRED_TOOLS="wget unzip xz-utils parted kpartx e2fsprogs dosfstools sudo"
for cmd in $REQUIRED_TOOLS; do
    if ! command -v $cmd &> /dev/null && ! dpkg -l | grep -q "^ii.*$cmd"; then
        echo "ERROR: Required tool '$cmd' not found"
        echo "Install with: sudo apt-get install $REQUIRED_TOOLS"
        exit 1
    fi
done

# Function to build image for a specific platform
build_platform_image() {
    local platform=$1
    local base_image="${PLATFORMS[$platform]}"
    local download_url="${DOWNLOAD_URLS[$platform]}"
    
    echo "=========================================="
    echo "Building for platform: $platform"
    echo "Base image: $base_image"
    echo "=========================================="
    
    # Create platform-specific work directory
    local platform_dir="$WORK_DIR/$platform"
    mkdir -p "$platform_dir"
    cd "$platform_dir"
    
    # Determine file extension and download URL
    local image_file=""
    local zip_file=""
    local full_url=""
    
    if [[ $base_image == *"raspios"* ]]; then
        image_file="${base_image}.img"
        zip_file="${base_image}.img.xz"
        full_url="${download_url}${zip_file}"
    elif [[ $base_image == *"ubuntu"* ]]; then
        image_file="${base_image}.img"
        zip_file="${base_image}.img.xz"
        full_url="${download_url}${zip_file}"
    fi
    
    # Download base image if needed
    if [ ! -f "$image_file" ]; then
        echo "Downloading $platform base image..."
        if [ ! -f "$zip_file" ]; then
            echo "Downloading from: $full_url"
            wget "$full_url" -O "$zip_file" || {
                echo "WARNING: Failed to download $zip_file, skipping $platform"
                return 1
            }
        fi
        
        echo "Extracting $zip_file..."
        if [[ $zip_file == *.xz ]]; then
            unxz -k "$zip_file"
        elif [[ $zip_file == *.gz ]]; then
            gunzip -k "$zip_file"
        fi
    fi
    
    # Create output image name
    local output_image="collatz-network-${platform}-${DATE_STAMP}.img"
    
    # Copy base image
    echo "Creating custom image: $output_image"
    cp "$image_file" "$output_image"
    
    # Expand image to add space for Collatz files
    echo "Expanding image (adding 1GB)..."
    dd if=/dev/zero bs=1M count=1024 >> "$output_image"
    
    # Set up loop device and resize partition
    echo "Setting up loop device..."
    local loop_device=$(sudo losetup -f --show "$output_image")
    sudo kpartx -a "$loop_device"
    
    # Get partition names (handle different naming schemes)
    local boot_part=""
    local root_part=""
    
    # Try different partition naming schemes
    if [ -e "/dev/mapper/$(basename ${loop_device})p1" ]; then
        boot_part="/dev/mapper/$(basename ${loop_device})p1"
        root_part="/dev/mapper/$(basename ${loop_device})p2"
    elif [ -e "/dev/mapper/$(basename ${loop_device})1" ]; then
        boot_part="/dev/mapper/$(basename ${loop_device})1"
        root_part="/dev/mapper/$(basename ${loop_device})2"
    else
        echo "ERROR: Could not find partition mappings"
        sudo kpartx -d "$loop_device"
        sudo losetup -d "$loop_device"
        return 1
    fi
    
    # Resize partition table and filesystem
    echo "Resizing partition..."
    sudo parted "$output_image" resizepart 2 100% || true
    
    # Check and resize filesystem
    sudo e2fsck -f "$root_part" || true
    sudo resize2fs "$root_part"
    
    # Mount partitions
    local mount_boot="./mount/boot"
    local mount_root="./mount/root"
    mkdir -p "$mount_boot" "$mount_root"
    
    sudo mount "$boot_part" "$mount_boot"
    sudo mount "$root_part" "$mount_root"
    
    echo "✓ Image mounted for $platform"
    
    # Install Collatz Network
    install_collatz_network "$platform" "$mount_boot" "$mount_root"
    
    # Cleanup
    echo "Cleaning up mounts..."
    sudo umount "$mount_boot" "$mount_root" || true
    sudo kpartx -d "$loop_device"
    sudo losetup -d "$loop_device"
    
    echo "✓ Completed build for $platform: $output_image"
    echo "  Image location: $platform_dir/$output_image"
    echo
    
    cd "$WORK_DIR"
}

# Function to install Collatz Network on mounted filesystem
install_collatz_network() {
    local platform=$1
    local mount_boot=$2
    local mount_root=$3
    
    echo "Installing Collatz Network for $platform..."
    
    # Enable SSH
    echo "  - Enabling SSH..."
    sudo touch "$mount_boot/ssh"
    
    # Configure Wi-Fi template
    echo "  - Creating Wi-Fi configuration template..."
    sudo tee "$mount_boot/wpa_supplicant.conf.template" > /dev/null << 'EOF'
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

# Example network configuration - edit with your details
network={
    ssid="YOUR_WIFI_SSID"
    psk="YOUR_WIFI_PASSWORD"
    key_mgmt=WPA-PSK
}
EOF
    
    # Create user directory
    local user_home=""
    if [[ $platform == *"ubuntu"* ]]; then
        user_home="$mount_root/home/ubuntu"
        sudo mkdir -p "$user_home"
    else
        user_home="$mount_root/home/pi" 
        sudo mkdir -p "$user_home"
    fi
    
    # Clone Collatz Network
    echo "  - Installing Collatz Network..."
    sudo git clone /workspace "$user_home/collatz-network" || {
        echo "    Copying files manually..."
        sudo mkdir -p "$user_home/collatz-network"
        sudo cp -r /workspace/* "$user_home/collatz-network/" 2>/dev/null || true
    }
    
    # Set ownership
    if [[ $platform == *"ubuntu"* ]]; then
        sudo chown -R 1000:1000 "$user_home"
    else
        sudo chown -R 1000:1000 "$user_home"  # pi user UID typically 1000
    fi
    
    # Install Python dependencies script
    echo "  - Creating dependency installation script..."
    sudo tee "$user_home/collatz-network/install-deps.sh" > /dev/null << 'EOF'
#!/bin/bash
set -e

echo "Installing Collatz Network dependencies..."

# Update system
sudo apt-get update
sudo apt-get install -y python3 python3-pip git curl

# Install Python dependencies
cd /home/$(whoami)/collatz-network
pip3 install --user -r requirements_distributed.txt

# Install IPFS
echo "Installing IPFS..."
cd /tmp
IPFS_VERSION="v0.31.0"
ARCH=$(uname -m)

if [[ $ARCH == "aarch64" ]]; then
    IPFS_ARCH="arm64"
elif [[ $ARCH == "armv7l" ]]; then
    IPFS_ARCH="arm"
else
    IPFS_ARCH="amd64"
fi

wget "https://dist.ipfs.tech/kubo/${IPFS_VERSION}/kubo_${IPFS_VERSION}_linux-${IPFS_ARCH}.tar.gz"
tar -xzf "kubo_${IPFS_VERSION}_linux-${IPFS_ARCH}.tar.gz"
sudo ./kubo/install.sh

# Initialize IPFS
ipfs init

echo "✓ Collatz Network dependencies installed!"
echo "Run 'python3 network_launcher.py' to start"
EOF
    
    sudo chmod +x "$user_home/collatz-network/install-deps.sh"
    
    # Create systemd service for auto-start
    echo "  - Creating systemd service..."
    sudo tee "$mount_root/etc/systemd/system/collatz-network.service" > /dev/null << EOF
[Unit]
Description=Collatz Distributed Network Worker
After=network.target
Wants=network.target

[Service]
Type=simple
User=$(if [[ $platform == *"ubuntu"* ]]; then echo "ubuntu"; else echo "pi"; fi)
WorkingDirectory=$user_home/collatz-network
ExecStart=/usr/bin/python3 network_launcher.py
Restart=always
RestartSec=10
Environment=PATH=/usr/bin:/usr/local/bin

[Install]
WantedBy=multi-user.target
EOF
    
    # Create first-boot setup script
    echo "  - Creating first-boot setup..."
    sudo tee "$mount_root/etc/rc.local" > /dev/null << 'EOF'
#!/bin/sh -e
#
# This script runs on first boot to set up Collatz Network

if [ -f /home/*/collatz-network/install-deps.sh ] && [ ! -f /var/lib/collatz-setup-done ]; then
    echo "Setting up Collatz Network on first boot..."
    
    # Find the user home directory
    USER_HOME=$(find /home -maxdepth 1 -type d -name "*" | grep -v "^/home$" | head -1)
    
    if [ -n "$USER_HOME" ]; then
        cd "$USER_HOME/collatz-network"
        sudo -u $(basename "$USER_HOME") ./install-deps.sh
        
        # Mark setup as complete
        touch /var/lib/collatz-setup-done
        
        echo "✓ Collatz Network setup complete!"
        echo "Access via SSH and run: cd ~/collatz-network && python3 network_launcher.py"
    fi
fi

exit 0
EOF
    
    sudo chmod +x "$mount_root/etc/rc.local"
    
    # Create README for users
    sudo tee "$user_home/README-COLLATZ.txt" > /dev/null << 'EOF'
Collatz Distributed Network - Pre-installed Image

This image comes with the Collatz Network pre-installed and ready to use.

Quick Start:
1. Boot your device and wait for first-time setup (may take 5-10 minutes)
2. Connect via SSH (user: pi/ubuntu, default password: raspberry/ubuntu)  
3. Run: cd ~/collatz-network && python3 network_launcher.py
4. Create an account (option 4) then start mining (option 1)

Network Info:
- The network searches for counterexamples to the Collatz Conjecture
- Your device will contribute computational power to the distributed search
- All results are verified and stored on IPFS for transparency
- Join thousands of other nodes in this mathematical quest!

Configuration:
- Edit wpa_supplicant.conf in /boot for Wi-Fi setup
- SSH is enabled by default
- IPFS and Python dependencies install automatically on first boot

Support: https://github.com/Jaylouisw/ProjectCollatz
EOF
    
    echo "  ✓ Collatz Network installation complete for $platform"
}

# Create work directory
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# Main execution logic
if [ "$BUILD_ALL" = true ]; then
    echo "Building images for ALL supported platforms..."
    echo
    
    failed_builds=()
    successful_builds=()
    
    for platform in "${!PLATFORMS[@]}"; do
        if build_platform_image "$platform"; then
            successful_builds+=("$platform")
        else
            failed_builds+=("$platform")
        fi
    done
    
    # Final summary
    echo "=========================================="
    echo "  Build Summary"
    echo "=========================================="
    echo
    echo "Successful builds (${#successful_builds[@]}):"
    for platform in "${successful_builds[@]}"; do
        echo "  ✓ $platform"
        # Find and list the output file
        output_file=$(find "$WORK_DIR/$platform" -name "collatz-network-${platform}-*.img" 2>/dev/null | head -1)
        if [ -n "$output_file" ]; then
            echo "    → $(basename "$output_file")"
        fi
    done
    
    if [ ${#failed_builds[@]} -gt 0 ]; then
        echo
        echo "Failed builds (${#failed_builds[@]}):"
        for platform in "${failed_builds[@]}"; do
            echo "  ✗ $platform"
        done
    fi
    
else
    # Build single platform
    if [[ -z "${PLATFORMS[$PLATFORM]}" ]]; then
        echo "ERROR: Unknown platform '$PLATFORM'"
        echo "Available platforms: ${!PLATFORMS[@]}"
        exit 1
    fi
    
    build_platform_image "$PLATFORM"
fi

echo
echo "=========================================="
echo "  Multi-Platform Build Complete!"
echo "=========================================="
echo
echo "Images are located in: $WORK_DIR/<platform>/"
echo
echo "To write to SD card (replace /dev/sdX):"
echo "  xzcat <image_file> | sudo dd of=/dev/sdX bs=4M status=progress"
echo
echo "Or use Etcher: https://www.balena.io/etcher/"
echo
echo "Supported devices by platform:"
echo "  rpi4-arm64:   Raspberry Pi 4, Pi 400, CM4 (64-bit)"
echo "  rpi4-arm32:   Raspberry Pi 4, Pi 400, CM4 (32-bit)" 
echo "  rpi3-arm64:   Raspberry Pi 3, 3A+, 3B+ (64-bit)"
echo "  rpi3-arm32:   Raspberry Pi 3, 3A+, 3B+ (32-bit)" 
echo "  rpi-zero2:    Raspberry Pi Zero 2 W (64-bit)"
echo "  rpi-legacy:   Raspberry Pi 1, 2, Zero (32-bit only)"
echo "  ubuntu-arm64: Orange Pi, Rock Pi, Odroid (64-bit)"
echo "  ubuntu-arm32: Older ARM32 SBCs"
echo
EOF
    
    echo "  ✓ Collatz Network installation complete for $platform"
}
    psk="YOUR_WIFI_PASSWORD"
    key_mgmt=WPA-PSK
}
EOF

sudo cp wpa_supplicant.conf.template "$MOUNT_BOOT/"

# Install Collatz Network
echo "Installing Collatz Network..."

# Clone repository
sudo git clone https://github.com/Jaylouisw/ProjectCollatz.git "$MOUNT_ROOT/home/pi/collatz-network"

# Install dependencies script
cat > install-deps.sh << 'EOF'
#!/bin/bash
# Run on first boot to install dependencies

set -e

echo "Installing Collatz Network dependencies..."

# Update system
apt-get update
apt-get upgrade -y

# Install Python and dependencies
apt-get install -y python3 python3-pip git

# Install IPFS
IPFS_VERSION="v0.24.0"
wget "https://dist.ipfs.tech/kubo/${IPFS_VERSION}/kubo_${IPFS_VERSION}_linux-arm64.tar.gz" -O /tmp/ipfs.tar.gz
tar -xvzf /tmp/ipfs.tar.gz -C /tmp
mv /tmp/kubo/ipfs /usr/local/bin/ipfs
rm -rf /tmp/ipfs.tar.gz /tmp/kubo

# Install Python packages
cd /home/pi/collatz-network
pip3 install --break-system-packages -r requirements_distributed.txt

# Initialize IPFS for pi user
sudo -u pi ipfs init

# Set ownership
chown -R pi:pi /home/pi/collatz-network

echo "✓ Dependencies installed"

# Remove this script
rm /usr/local/bin/install-collatz-deps.sh
EOF

sudo cp install-deps.sh "$MOUNT_ROOT/usr/local/bin/install-collatz-deps.sh"
sudo chmod +x "$MOUNT_ROOT/usr/local/bin/install-collatz-deps.sh"

# Create systemd service for auto-start
echo "Creating systemd service..."
cat > collatz-network.service << 'EOF'
[Unit]
Description=Collatz Distributed Network Worker
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/collatz-network
ExecStartPre=/usr/local/bin/ipfs daemon --init &
ExecStart=/usr/bin/python3 /home/pi/collatz-network/distributed_collatz.py --cpu-only
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo cp collatz-network.service "$MOUNT_ROOT/etc/systemd/system/"

# Enable service (will start on boot after first-boot setup)
sudo chroot "$MOUNT_ROOT" systemctl enable collatz-network

# Create first-boot setup script
cat > first-boot-setup.sh << 'EOF'
#!/bin/bash
# First boot setup script

# Check if already run
if [ -f /var/lib/collatz-first-boot-done ]; then
    exit 0
fi

# Install dependencies
/usr/local/bin/install-collatz-deps.sh

# Mark as done
touch /var/lib/collatz-first-boot-done

# Reboot to start service
reboot
EOF

sudo cp first-boot-setup.sh "$MOUNT_ROOT/usr/local/bin/first-boot-setup.sh"
sudo chmod +x "$MOUNT_ROOT/usr/local/bin/first-boot-setup.sh"

# Add to rc.local for first boot
sudo sed -i 's/^exit 0/\/usr\/local\/bin\/first-boot-setup.sh\nexit 0/' "$MOUNT_ROOT/etc/rc.local"

# Create README
cat > README-COLLATZ.txt << 'EOF'
========================================
  Collatz Network - Raspberry Pi Image
========================================

This Raspberry Pi image includes:
- Raspbian Lite (headless, no GUI)
- Collatz Distributed Network pre-installed
- Auto-starts on boot

FIRST BOOT:
-----------
On first boot, the Pi will:
1. Install all dependencies (takes ~10 minutes)
2. Automatically reboot
3. Start the Collatz worker node

Default credentials:
  Username: pi
  Password: raspberry
  (CHANGE THIS IMMEDIATELY!)

SSH is enabled by default.

WI-FI SETUP:
-----------
Before first boot, edit /boot/wpa_supplicant.conf.template
with your Wi-Fi credentials and rename to wpa_supplicant.conf

MANUAL CONTROL:
--------------
SSH into the Pi:
  ssh pi@raspberrypi.local

Check service status:
  sudo systemctl status collatz-network

Stop/start service:
  sudo systemctl stop collatz-network
  sudo systemctl start collatz-network

View logs:
  journalctl -u collatz-network -f

Manual operation:
  cd /home/pi/collatz-network
  python3 network_launcher.py

CREATING A USER ACCOUNT:
-----------------------
SSH into the Pi and run:
  cd /home/pi/collatz-network
  python3 user_account.py create <username>

Then edit /etc/systemd/system/collatz-network.service
to add: --user-key /home/pi/collatz-network/keys/user_<username>_private.pem

Reload and restart:
  sudo systemctl daemon-reload
  sudo systemctl restart collatz-network

NETWORK INFO:
------------
Find your Pi's contribution:
  python3 user_account.py stats <user_id>

View leaderboard:
  python3 user_account.py leaderboard

UPDATES:
-------
Update the Collatz software:
  cd /home/pi/collatz-network
  git pull
  sudo systemctl restart collatz-network

SUPPORT:
-------
GitHub: https://github.com/Jaylouisw/ProjectCollatz
EOF

sudo cp README-COLLATZ.txt "$MOUNT_ROOT/home/pi/"
sudo chown 1000:1000 "$MOUNT_ROOT/home/pi/README-COLLATZ.txt"

echo "✓ Collatz Network installed"
echo

# Unmount
echo "Unmounting image..."
sudo umount "$MOUNT_BOOT"
sudo umount "$MOUNT_ROOT"
sudo kpartx -d "$LOOP_DEVICE"
sudo losetup -d "$LOOP_DEVICE"

# Compress image
echo "Compressing image..."
xz -9 -v "$OUTPUT_IMAGE"

echo
echo "=========================================="
echo "  Build Complete!"
echo "=========================================="
echo
echo "Output image: $OUTPUT_IMAGE.xz"
echo
echo "To write to SD card (replace /dev/sdX):"
echo "  xzcat $OUTPUT_IMAGE.xz | sudo dd of=/dev/sdX bs=4M status=progress"
echo
echo "Or use Etcher: https://www.balena.io/etcher/"
echo
