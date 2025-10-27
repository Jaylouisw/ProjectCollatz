#!/bin/bash
# Test script to validate GitHub Actions workflow locally

set -e

echo "=========================================="
echo "  GitHub Actions Workflow Validator"
echo "=========================================="
echo

# Check if we have the required tools
echo "Checking prerequisites..."

if ! command -v yamllint &> /dev/null; then
    echo "Installing yamllint..."
    pip3 install --user yamllint || {
        echo "Warning: Could not install yamllint. Skipping YAML validation."
        SKIP_YAML=1
    }
fi

if ! command -v shellcheck &> /dev/null; then
    echo "Warning: shellcheck not found. Install with: sudo apt install shellcheck"
    SKIP_SHELL=1
fi

echo "✓ Prerequisites checked"
echo

# Validate workflow YAML files
if [[ -z "$SKIP_YAML" ]]; then
    echo "Validating workflow YAML files..."
    
    for workflow in .github/workflows/*.yml; do
        echo "  Checking $workflow..."
        yamllint "$workflow" && echo "    ✓ Valid YAML" || echo "    ✗ YAML errors found"
    done
    echo
fi

# Validate shell scripts
if [[ -z "$SKIP_SHELL" ]]; then
    echo "Validating shell scripts..."
    
    if [ -f "build-pi-image.sh" ]; then
        echo "  Checking build-pi-image.sh..."
        shellcheck build-pi-image.sh && echo "    ✓ No shell issues" || echo "    ✗ Shell issues found"
    fi
    
    if [ -f "install.sh" ]; then
        echo "  Checking install.sh..."
        shellcheck install.sh && echo "    ✓ No shell issues" || echo "    ✗ Shell issues found"
    fi
    echo
fi

# Test build script syntax
echo "Testing build script..."
if [ -f "build-pi-image.sh" ]; then
    chmod +x build-pi-image.sh
    bash -n build-pi-image.sh && echo "  ✓ Script syntax valid" || echo "  ✗ Script syntax errors"
    
    # Test help output
    echo "  Testing help output..."
    ./build-pi-image.sh --help >/dev/null && echo "  ✓ Help command works" || echo "  ✗ Help command failed"
else
    echo "  ✗ build-pi-image.sh not found"
fi
echo

# Check for required workflow files
echo "Checking workflow files..."
WORKFLOWS=(
    "build-sbc-images.yml"
    "test-build.yml" 
    "update-downloads.yml"
    "badge.yml"
)

for workflow in "${WORKFLOWS[@]}"; do
    if [ -f ".github/workflows/$workflow" ]; then
        echo "  ✓ $workflow found"
    else
        echo "  ✗ $workflow missing"
    fi
done
echo

# Validate platform configurations
echo "Validating platform configurations..."
if grep -q "PLATFORMS:" .github/workflows/build-sbc-images.yml; then
    PLATFORMS=$(grep "PLATFORMS:" .github/workflows/build-sbc-images.yml | cut -d"'" -f2)
    echo "  Configured platforms: $PLATFORMS"
    echo "  ✓ Platform configuration found"
else
    echo "  ✗ Platform configuration not found"
fi
echo

# Check README integration
echo "Checking README integration..."
if grep -q "Pre-Built SBC Images" README.md; then
    echo "  ✓ SBC images section found in README"
else
    echo "  ✗ SBC images section missing from README"
fi

if grep -q "img.shields.io/badge/SBC" README.md; then
    echo "  ✓ Build status badge found in README"  
else
    echo "  ✗ Build status badge missing from README"
fi
echo

echo "=========================================="
echo "  Validation Complete"
echo "=========================================="
echo
echo "To trigger a test build:"
echo "  1. Push to a branch with workflow changes"
echo "  2. Open a PR to test the test-build workflow"
echo "  3. Create a tag/release to test full build workflow"
echo
echo "Manual workflow trigger:"
echo "  Go to Actions → Build Multi-Platform SBC Images → Run workflow"
echo