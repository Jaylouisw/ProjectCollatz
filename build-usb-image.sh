#!/bin/bash
# Collatz Network - Bootable USB Image Builder
# Creates x86_64 USB images with Collatz Network pre-installed
# Based on Ubuntu Desktop Live USB with persistence

set -e

# Configuration
WORK_DIR="./usb-build"
DATE_STAMP=$(date +%Y%m%d)
USB_SIZE="4096"  # 4GB USB image size in MB
PERSISTENCE_SIZE="1024"  # 1GB for persistence

# Ubuntu versions for USB images
declare -A USB_PLATFORMS=(
    ["ubuntu-x86_64-desktop"]="ubuntu-22.04.3-desktop-amd64"
    ["ubuntu-x86_64-server"]="ubuntu-22.04.3-live-server-amd64"
)

declare -A USB_DOWNLOAD_URLS=(
    ["ubuntu-x86_64-desktop"]="https://releases.ubuntu.com/22.04/"
    ["ubuntu-x86_64-server"]="https://releases.ubuntu.com/22.04/"
)

# Default configuration
DEFAULT_PLATFORM="ubuntu-x86_64-desktop"
PLATFORM="$DEFAULT_PLATFORM"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --platform=*)
            PLATFORM="${1#*=}"
            shift
            ;;
        --size=*)
            USB_SIZE="${1#*=}"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --platform=PLATFORM    Platform to build (default: $DEFAULT_PLATFORM)"
            echo "  --size=SIZE           USB image size in MB (default: $USB_SIZE)"
            echo ""
            echo "Available platforms:"
            for platform in "${!USB_PLATFORMS[@]}"; do
                echo "  - $platform"
            done
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate platform
if [[ ! ${USB_PLATFORMS[$PLATFORM]+_} ]]; then
    echo "❌ Error: Unknown platform '$PLATFORM'"
    echo "Available platforms: ${!USB_PLATFORMS[*]}"
    exit 1
fi

# System requirements check
check_requirements() {
    echo "🔍 Checking system requirements..."
    
    local missing_tools=()
    
    # Required tools for USB image building
    for tool in wget curl xz-utils genisoimage mtools syslinux-utils dosfstools parted kpartx losetup; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        echo "❌ Missing required tools: ${missing_tools[*]}"
        echo "Install with: sudo apt-get install ${missing_tools[*]}"
        exit 1
    fi
    
    # Check available disk space (need at least 8GB)
    local available_space_kb=$(df . | tail -1 | awk '{print $4}')
    local available_space_gb=$((available_space_kb / 1024 / 1024))
    
    if [[ $available_space_gb -lt 8 ]]; then
        echo "❌ Insufficient disk space. Need at least 8GB, have ${available_space_gb}GB"
        exit 1
    fi
    
    echo "✅ System requirements check passed"
}

# Download base Ubuntu ISO
download_base_iso() {
    local iso_name="${USB_PLATFORMS[$PLATFORM]}"
    local download_url="${USB_DOWNLOAD_URLS[$PLATFORM]}"
    local iso_file="${iso_name}.iso"
    
    echo "📥 Downloading base ISO: $iso_name"
    
    mkdir -p "$WORK_DIR/$PLATFORM/downloads"
    cd "$WORK_DIR/$PLATFORM/downloads"
    
    if [[ ! -f "$iso_file" ]]; then
        echo "Downloading from $download_url"
        wget -c "${download_url}${iso_file}" || {
            echo "❌ Failed to download ISO"
            exit 1
        }
    else
        echo "✅ ISO already downloaded: $iso_file"
    fi
    
    # Verify ISO (basic check)
    if [[ ! -s "$iso_file" ]]; then
        echo "❌ Downloaded ISO appears to be empty or corrupt"
        exit 1
    fi
    
    cd - > /dev/null
    echo "✅ Base ISO ready: $iso_file"
}

# Extract and customize ISO
customize_iso() {
    local iso_name="${USB_PLATFORMS[$PLATFORM]}"
    local iso_file="$WORK_DIR/$PLATFORM/downloads/${iso_name}.iso"
    local extract_dir="$WORK_DIR/$PLATFORM/iso-extract"
    local custom_dir="$WORK_DIR/$PLATFORM/iso-custom"
    
    echo "🔧 Customizing ISO with Collatz Network..."
    
    # Clean previous extractions
    sudo rm -rf "$extract_dir" "$custom_dir" 2>/dev/null || true
    mkdir -p "$extract_dir" "$custom_dir"
    
    # Extract ISO
    echo "Extracting ISO..."
    sudo mount -o loop "$iso_file" "$extract_dir"
    
    # Copy contents to writable directory
    echo "Copying ISO contents..."
    sudo cp -rT "$extract_dir" "$custom_dir"
    sudo umount "$extract_dir"
    
    # Make writable
    sudo chmod -R u+w "$custom_dir"
    
    # Create Collatz Network installation script
    cat > "$custom_dir/collatz-setup.sh" << 'EOF'
#!/bin/bash
# Collatz Network Auto-Setup for Live USB

set -e

# Wait for network
echo "Waiting for network connection..."
for i in {1..30}; do
    if ping -c 1 github.com >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

# Install dependencies
echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip git curl

# Download Collatz Network
echo "Downloading Collatz Network..."
cd /home/ubuntu || cd /home/user || cd /tmp
git clone https://github.com/Jaylouisw/ProjectCollatz.git collatz-network
cd collatz-network

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements_distributed.txt

# Install IPFS
echo "Installing IPFS..."
./install.sh --ipfs-only

# Create desktop shortcut
if [[ -d "/home/ubuntu/Desktop" ]]; then
    cat > "/home/ubuntu/Desktop/Collatz Network.desktop" << 'SHORTCUT'
[Desktop Entry]
Version=1.0
Type=Application
Name=Collatz Network
Comment=Start Collatz Distributed Network
Exec=gnome-terminal -- bash -c "cd /home/ubuntu/collatz-network && python3 network_launcher.py; exec bash"
Icon=applications-science
Terminal=false
Categories=Science;Education;
SHORTCUT
    chmod +x "/home/ubuntu/Desktop/Collatz Network.desktop"
fi

echo "✅ Collatz Network setup complete!"
echo "Run: cd ~/collatz-network && python3 network_launcher.py"
EOF

    chmod +x "$custom_dir/collatz-setup.sh"
    
    # Modify boot configuration for auto-setup
    if [[ -f "$custom_dir/boot/grub/grub.cfg" ]]; then
        # Add Collatz Network boot option
        sed -i '/^menuentry.*Ubuntu.*/{
            a\
menuentry "Ubuntu with Collatz Network" {\
    set gfxpayload=keep\
    linux   /casper/vmlinuz boot=casper quiet splash --- /collatz-setup.sh\
    initrd  /casper/initrd\
}
        }' "$custom_dir/boot/grub/grub.cfg"
    fi
    
    echo "✅ ISO customization complete"
}

# Create bootable USB image
create_usb_image() {
    local output_name="collatz-network-${PLATFORM}-${DATE_STAMP}.img"
    local output_path="$WORK_DIR/$PLATFORM/$output_name"
    local custom_dir="$WORK_DIR/$PLATFORM/iso-custom"
    
    echo "🔨 Creating bootable USB image..."
    
    # Create empty image file
    echo "Creating ${USB_SIZE}MB image file..."
    dd if=/dev/zero of="$output_path" bs=1M count="$USB_SIZE" status=progress
    
    # Create partition table
    echo "Creating partition table..."
    parted "$output_path" --script mklabel msdos
    parted "$output_path" --script mkpart primary fat32 1MiB 100%
    parted "$output_path" --script set 1 boot on
    
    # Setup loop device
    local loop_device
    loop_device=$(sudo losetup --find --partscan --show "$output_path")
    local partition="${loop_device}p1"
    
    echo "Using loop device: $loop_device"
    
    # Format partition
    echo "Formatting USB partition..."
    sudo mkfs.vfat -F32 -n "COLLATZ" "$partition"
    
    # Mount and copy files
    local mount_point="/tmp/usb-mount-$$"
    sudo mkdir -p "$mount_point"
    sudo mount "$partition" "$mount_point"
    
    echo "Copying files to USB..."
    sudo cp -r "$custom_dir"/* "$mount_point/"
    
    # Install syslinux bootloader
    echo "Installing bootloader..."
    sudo syslinux --install "$partition"
    
    # Create syslinux config
    sudo tee "$mount_point/syslinux.cfg" > /dev/null << EOF
DEFAULT ubuntu
PROMPT 1
TIMEOUT 30

LABEL ubuntu
    MENU LABEL Ubuntu with Collatz Network
    KERNEL /casper/vmlinuz
    APPEND boot=casper initrd=/casper/initrd quiet splash ---

LABEL ubuntu-safe
    MENU LABEL Ubuntu (Safe Mode)
    KERNEL /casper/vmlinuz
    APPEND boot=casper initrd=/casper/initrd nomodeset
EOF
    
    # Cleanup
    sudo umount "$mount_point"
    sudo rmdir "$mount_point"
    sudo losetup -d "$loop_device"
    
    # Compress image
    echo "Compressing image..."
    xz -9 "$output_path"
    
    # Generate checksum
    cd "$WORK_DIR/$PLATFORM"
    sha256sum "${output_name}.xz" > "${output_name}.xz.sha256"
    cd - > /dev/null
    
    echo "✅ USB image created: ${output_path}.xz"
    echo "✅ Checksum: ${output_path}.xz.sha256"
}

# Main build function
build_usb_image() {
    echo "🚀 Building Collatz Network USB Image"
    echo "Platform: $PLATFORM"
    echo "Size: ${USB_SIZE}MB"
    echo "Working directory: $WORK_DIR"
    echo ""
    
    # Create working directory
    mkdir -p "$WORK_DIR/$PLATFORM"
    
    # Build steps
    check_requirements
    download_base_iso
    customize_iso
    create_usb_image
    
    echo ""
    echo "🎉 USB image build complete!"
    echo "Image: $WORK_DIR/$PLATFORM/collatz-network-${PLATFORM}-${DATE_STAMP}.img.xz"
    echo ""
    echo "To flash to USB:"
    echo "1. Verify: sha256sum -c collatz-network-${PLATFORM}-${DATE_STAMP}.img.xz.sha256"
    echo "2. Extract: xz -d collatz-network-${PLATFORM}-${DATE_STAMP}.img.xz"
    echo "3. Flash: sudo dd if=collatz-network-${PLATFORM}-${DATE_STAMP}.img of=/dev/sdX bs=4M status=progress"
    echo "   (Replace /dev/sdX with your USB device)"
}

# Show platform info
show_info() {
    echo "Collatz Network USB Image Builder"
    echo "================================="
    echo ""
    echo "Available platforms:"
    for platform in "${!USB_PLATFORMS[@]}"; do
        echo "  🖥️  $platform - ${USB_PLATFORMS[$platform]}"
    done
    echo ""
    echo "Current platform: $PLATFORM"
    echo "Image size: ${USB_SIZE}MB"
}

# Main execution
main() {
    show_info
    echo ""
    
    if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
        build_usb_image
    fi
}

# Allow script to be sourced for testing
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi