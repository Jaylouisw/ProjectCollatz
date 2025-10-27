# build-pi-docker.ps1
# Builds Raspberry Pi images using Docker on Windows
# This script creates a Docker container with all Linux tools needed for Pi image building

param(
    [switch]$BuildOnly,     # Only build the Docker image, don't run it
    [switch]$Force,         # Force rebuild of Docker image
    [switch]$All,           # Build for all supported platforms
    [string]$Platform = "", # Build for specific platform
    [switch]$Help           # Show help message
)

Write-Host "=============================================="
Write-Host "  Collatz Multi-Platform Builder (Docker)"
Write-Host "=============================================="
Write-Host

if ($Help) {
    Write-Host "Usage: .\build-pi-docker.ps1 [options]"
    Write-Host
    Write-Host "Options:"
    Write-Host "  -BuildOnly          Only build Docker image, don't run"
    Write-Host "  -Force              Force rebuild of Docker image"
    Write-Host "  -All                Build for all supported platforms"
    Write-Host "  -Platform <name>    Build for specific platform"
    Write-Host "  -Help               Show this help message"
    Write-Host
    Write-Host "Available platforms:"
    Write-Host "  rpi4-arm64         Raspberry Pi 4/400/CM4 (64-bit)"
    Write-Host "  rpi4-arm32         Raspberry Pi 4/400/CM4 (32-bit)"
    Write-Host "  rpi3-arm64         Raspberry Pi 3/3B+ (64-bit)"
    Write-Host "  rpi3-arm32         Raspberry Pi 3/3B+ (32-bit)" 
    Write-Host "  rpi-zero2          Raspberry Pi Zero 2 W (64-bit)"
    Write-Host "  rpi-legacy         Raspberry Pi 1/2/Zero (32-bit only)"
    Write-Host "  ubuntu-arm64       Orange Pi, Rock Pi, Odroid (64-bit)"
    Write-Host "  ubuntu-arm32       Older ARM32 SBCs"
    Write-Host
    Write-Host "Examples:"
    Write-Host "  .\build-pi-docker.ps1 -All"
    Write-Host "  .\build-pi-docker.ps1 -Platform rpi3-arm64"
    Write-Host "  .\build-pi-docker.ps1 -Platform ubuntu-arm64 -Force"
    exit 0
}

# Check if Docker is available
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker found: $dockerVersion"
} catch {
    Write-Host "❌ ERROR: Docker not found"
    Write-Host "   Please install Docker Desktop for Windows"
    Write-Host "   Download from: https://www.docker.com/products/docker-desktop"
    exit 1
}

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✓ Docker daemon is running"
} catch {
    Write-Host "❌ ERROR: Docker daemon not running"
    Write-Host "   Please start Docker Desktop"
    exit 1
}

Write-Host

# Build Docker image
$imageName = "collatz-pi-builder"
$imageExists = docker images -q $imageName

if ($Force -or -not $imageExists) {
    Write-Host "Building Docker image for Pi building..."
    Write-Host "This may take several minutes on first run..."
    Write-Host
    
    docker build -f Dockerfile.pi-builder -t $imageName .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ ERROR: Docker image build failed"
        exit 1
    }
    
    Write-Host "✓ Docker image built successfully"
} else {
    Write-Host "✓ Docker image already exists (use -Force to rebuild)"
}

if ($BuildOnly) {
    Write-Host
    Write-Host "Docker image ready. To run the Pi builder:"
    Write-Host "   docker run --privileged -v ${PWD}:/workspace $imageName"
    exit 0
}

Write-Host
Write-Host "Starting multi-platform image build in Docker container..."
Write-Host "Note: This requires privileged access to mount filesystems"
Write-Host

# Build command arguments
$dockerArgs = @("run", "--privileged", "--rm", "-v", "${PWD}:/workspace", $imageName)

if ($All) {
    Write-Host "Building for ALL supported platforms..."
    $dockerArgs += "--all"
} elseif ($Platform) {
    Write-Host "Building for platform: $Platform"
    $dockerArgs += "--platform=$Platform"
} else {
    Write-Host "Building for default platform (rpi4-arm64)..."
    Write-Host "Use -All to build all platforms or -Platform <name> for specific platform"
}

Write-Host

# Run the container
& docker @dockerArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host
    Write-Host "✓ Multi-platform image build completed successfully!"
    Write-Host "Built images are in the 'pi-build' directory:"
    Write-Host
    
    # List generated images
    if (Test-Path "pi-build") {
        Get-ChildItem -Path "pi-build" -Recurse -Filter "*.img" | ForEach-Object {
            $relativePath = $_.FullName.Replace((Get-Location), ".")
            Write-Host "  $relativePath"
        }
    }
    
    Write-Host
    Write-Host "To write to SD card:"
    Write-Host "  1. Use Etcher: https://www.balena.io/etcher/"
    Write-Host "  2. Or use dd: xzcat <image.xz> | sudo dd of=/dev/sdX bs=4M"
    
} else {
    Write-Host
    Write-Host "❌ Multi-platform image build failed"
    Write-Host "Check the output above for error details"
}