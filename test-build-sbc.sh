#!/bin/bash
# Test script to validate SBC image building process
# This is a simplified version for testing the GitHub Actions workflow

set -e

echo "=========================================="
echo "  Collatz Network - SBC Build Test"
echo "=========================================="

# Configuration
PLATFORM=${1:-"test-build"}
WORK_DIR="./pi-build"
DATE_STAMP=$(date +%Y%m%d)

# Create test environment
mkdir -p "$WORK_DIR/$PLATFORM"
cd "$WORK_DIR/$PLATFORM"

echo "Testing build process for platform: $PLATFORM"

# Check available space
echo "Available disk space:"
df -h

# Check required tools
echo "Checking required tools..."
MISSING_TOOLS=""
for cmd in wget unzip xz parted kpartx e2fsprogs dosfstools; do
    if ! command -v $cmd &> /dev/null; then
        MISSING_TOOLS="$MISSING_TOOLS $cmd"
    fi
done

if [ -n "$MISSING_TOOLS" ]; then
    echo "Missing tools:$MISSING_TOOLS"
    echo "Installing missing tools..."
    sudo apt-get update
    sudo apt-get install -y $MISSING_TOOLS
fi

# Create a minimal test image (100MB)
echo "Creating test image..."
TEST_IMAGE="collatz-network-$PLATFORM-$DATE_STAMP.img"

# Create a sparse file
dd if=/dev/zero of="$TEST_IMAGE" bs=1M count=0 seek=100
echo "Created test image: $TEST_IMAGE (100MB)"

# Add some test content
echo "Adding test content..."
mkdir -p test_content
echo "Collatz Network Test Image" > test_content/README.txt
echo "Platform: $PLATFORM" >> test_content/README.txt  
echo "Build Date: $(date)" >> test_content/README.txt
echo "Commit: ${GITHUB_SHA:-"local-build"}" >> test_content/README.txt

# Create a simple filesystem
echo "Creating filesystem..."
mkfs.ext4 -F "$TEST_IMAGE"

# Mount and add content
MOUNT_POINT=$(mktemp -d)
sudo mount "$TEST_IMAGE" "$MOUNT_POINT"
sudo cp -r test_content/* "$MOUNT_POINT/"
sudo umount "$MOUNT_POINT"
rmdir "$MOUNT_POINT"

echo "Test image created successfully: $TEST_IMAGE"
ls -lh "$TEST_IMAGE"

# Compress the image
echo "Compressing test image..."
xz -9 -v "$TEST_IMAGE"
COMPRESSED_IMAGE="$TEST_IMAGE.xz"

echo "Compressed image: $COMPRESSED_IMAGE"
ls -lh "$COMPRESSED_IMAGE"

# Generate checksum
sha256sum "$COMPRESSED_IMAGE" > "$COMPRESSED_IMAGE.sha256"
echo "Generated checksum: $COMPRESSED_IMAGE.sha256"

echo "=========================================="
echo "Build test completed successfully!"
echo "Output files:"
ls -lh *.img.xz *.sha256
echo "=========================================="