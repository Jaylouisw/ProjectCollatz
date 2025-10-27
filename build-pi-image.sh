#!/bin/bash
# Collatz Network - Raspberry Pi Image Builder
# Creates a Raspbian Lite image with Collatz Network pre-installed
# Tested on: Raspberry Pi 3, 4, Zero 2 W

set -e

echo "=========================================="
echo "  Collatz Network - Pi Image Builder"
echo "=========================================="
echo

# Check if running on Linux
if [ "$(uname -s)" != "Linux" ]; then
    echo "ERROR: This script must run on Linux"
    exit 1
fi

# Check for required tools
for cmd in wget unzip parted kpartx; do
    if ! command -v $cmd &> /dev/null; then
        echo "ERROR: Required tool '$cmd' not found"
        echo "Install with: sudo apt-get install $cmd"
        exit 1
    fi
done

# Configuration
RASPBIAN_VERSION="2024-03-15"
RASPBIAN_IMAGE="2024-03-15-raspios-bookworm-arm64-lite.img"
RASPBIAN_ZIP="${RASPBIAN_IMAGE}.xz"
RASPBIAN_URL="https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-${RASPBIAN_VERSION}/${RASPBIAN_ZIP}"

OUTPUT_IMAGE="collatz-network-pi-${RASPBIAN_VERSION}.img"
WORK_DIR="./pi-build"

# Create work directory
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# Download Raspbian if needed
if [ ! -f "$RASPBIAN_IMAGE" ]; then
    echo "Downloading Raspbian Lite..."
    if [ ! -f "$RASPBIAN_ZIP" ]; then
        wget "$RASPBIAN_URL" -O "$RASPBIAN_ZIP"
    fi
    
    echo "Extracting image..."
    unxz -k "$RASPBIAN_ZIP"
fi

# Copy base image
echo "Creating custom image..."
cp "$RASPBIAN_IMAGE" "$OUTPUT_IMAGE"

# Expand image to add our files
echo "Expanding image..."
dd if=/dev/zero bs=1M count=1024 >> "$OUTPUT_IMAGE"

# Resize partition
echo "Resizing partition..."
sudo parted "$OUTPUT_IMAGE" resizepart 2 100%

# Mount image
echo "Mounting image..."
LOOP_DEVICE=$(sudo losetup -f --show "$OUTPUT_IMAGE")
sudo kpartx -a "$LOOP_DEVICE"

# Get partition names
BOOT_PART="/dev/mapper/$(basename ${LOOP_DEVICE})p1"
ROOT_PART="/dev/mapper/$(basename ${LOOP_DEVICE})p2"

# Resize filesystem
sudo e2fsck -f "$ROOT_PART" || true
sudo resize2fs "$ROOT_PART"

# Mount partitions
MOUNT_BOOT="./mount/boot"
MOUNT_ROOT="./mount/root"
mkdir -p "$MOUNT_BOOT" "$MOUNT_ROOT"

sudo mount "$BOOT_PART" "$MOUNT_BOOT"
sudo mount "$ROOT_PART" "$MOUNT_ROOT"

echo "✓ Image mounted"
echo

# Enable SSH
echo "Enabling SSH..."
sudo touch "$MOUNT_BOOT/ssh"

# Configure Wi-Fi (optional - user can configure later)
echo "Creating Wi-Fi configuration template..."
cat > wpa_supplicant.conf.template << 'EOF'
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YOUR_WIFI_SSID"
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
