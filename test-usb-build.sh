#!/bin/bash
# Test script for USB image builder

set -e

echo "🧪 Testing USB Image Builder"

# Check if script exists and is readable
if [[ ! -f "build-usb-image.sh" ]]; then
    echo "❌ build-usb-image.sh not found"
    exit 1
fi

echo "✅ USB build script found"

# Test help output
echo "📖 Testing help output..."
if bash build-usb-image.sh --help | grep -q "Usage:"; then
    echo "✅ Help output working"
else
    echo "❌ Help output failed"
    exit 1
fi

# Test platform validation
echo "🔍 Testing platform validation..."
if bash build-usb-image.sh --platform=invalid-platform 2>&1 | grep -q "Unknown platform"; then
    echo "✅ Platform validation working"
else
    echo "❌ Platform validation failed"
    exit 1
fi

echo ""
echo "🎉 USB Image Builder tests passed!"
echo ""
echo "Available USB platforms:"
bash build-usb-image.sh --help | grep -A 10 "Available platforms:"