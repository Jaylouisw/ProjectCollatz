# Collatz Distributed Network - Windows Installer
# Single-command installation script
# Usage: iwr -useb https://raw.githubusercontent.com/Jaylouisw/ProjectCollatz/master/install.ps1 | iex

Write-Host "=========================================="
Write-Host "  Collatz Distributed Network Installer"
Write-Host "=========================================="
Write-Host ""

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python version: $pythonVersion"
    
    # Extract version number
    $versionMatch = [regex]::Match($pythonVersion, "Python (\d+)\.(\d+)")
    $major = [int]$versionMatch.Groups[1].Value
    $minor = [int]$versionMatch.Groups[2].Value
    
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
        Write-Host "ERROR: Python 3.8 or later is required" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✓ Python version OK" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python 3 is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from: https://www.python.org/downloads/"
    exit 1
}

Write-Host ""

# Create installation directory
$installDir = "$env:USERPROFILE\collatz-network"
Write-Host "Installation directory: $installDir"

if (Test-Path $installDir) {
    Write-Host "Directory already exists. Updating..."
} else {
    Write-Host "Creating directory..."
    New-Item -ItemType Directory -Path $installDir | Out-Null
}

Set-Location $installDir

# Check if git is installed
try {
    git --version | Out-Null
    $gitInstalled = $true
} catch {
    $gitInstalled = $false
}

# Clone or update repository
if (Test-Path ".git") {
    Write-Host "Updating existing installation..."
    git pull
} elseif ($gitInstalled) {
    Write-Host "Cloning repository..."
    git clone https://github.com/Jaylouisw/ProjectCollatz.git .
} else {
    Write-Host "Git not found. Downloading ZIP..."
    $zipUrl = "https://github.com/Jaylouisw/ProjectCollatz/archive/refs/heads/master.zip"
    $zipPath = "$env:TEMP\collatz.zip"
    
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath
    Expand-Archive -Path $zipPath -DestinationPath $env:TEMP -Force
    
    # Move files from extracted folder
    Get-ChildItem "$env:TEMP\ProjectCollatz-master" | Move-Item -Destination $installDir -Force
    
    Remove-Item $zipPath
    Remove-Item "$env:TEMP\ProjectCollatz-master" -Recurse -Force
}

Write-Host "✓ Repository cloned/updated" -ForegroundColor Green
Write-Host ""

# Install Python dependencies
Write-Host "Installing Python dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements_distributed.txt

Write-Host "✓ Python dependencies installed" -ForegroundColor Green
Write-Host ""

# Check for GPU support
Write-Host "Checking for GPU support..."
try {
    nvidia-smi | Out-Null
    Write-Host "NVIDIA GPU detected!" -ForegroundColor Yellow
    
    $installGpu = Read-Host "Install GPU support (CuPy)? [y/N]"
    if ($installGpu -eq 'y' -or $installGpu -eq 'Y') {
        # Try to detect CUDA version
        try {
            $nvsmi = nvidia-smi
            if ($nvsmi -match "CUDA Version: (\d+)\.(\d+)") {
                $cudaMajor = [int]$matches[1]
                Write-Host "CUDA version detected: $cudaMajor.x"
                
                if ($cudaMajor -ge 12) {
                    Write-Host "Installing CuPy for CUDA 12.x..."
                    python -m pip install cupy-cuda12x==13.0.0
                } else {
                    Write-Host "Installing CuPy for CUDA 11.x..."
                    python -m pip install cupy-cuda11x==13.0.0
                }
                Write-Host "✓ GPU support installed" -ForegroundColor Green
            }
        } catch {
            Write-Host "WARNING: Could not detect CUDA version" -ForegroundColor Yellow
            Write-Host "Please install CuPy manually: pip install cupy-cuda12x or cupy-cuda11x"
        }
    }
} catch {
    Write-Host "No NVIDIA GPU detected. Skipping GPU support."
    Write-Host "(CPU-only mode will be used)"
}

Write-Host ""

# Check for IPFS
Write-Host "Checking for IPFS..."
try {
    $ipfsVersion = ipfs --version 2>&1
    Write-Host "✓ IPFS already installed ($ipfsVersion)" -ForegroundColor Green
} catch {
    Write-Host "IPFS not found." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please install IPFS Desktop from:"
    Write-Host "https://github.com/ipfs/ipfs-desktop/releases"
    Write-Host ""
    Write-Host "Or install Kubo (command-line IPFS):"
    Write-Host "https://docs.ipfs.tech/install/"
    Write-Host ""
    
    $openBrowser = Read-Host "Open download page in browser? [Y/n]"
    if ($openBrowser -ne 'n' -and $openBrowser -ne 'N') {
        Start-Process "https://github.com/ipfs/ipfs-desktop/releases/latest"
    }
}

# Initialize IPFS if needed
if (Test-Path "$env:USERPROFILE\.ipfs") {
    Write-Host "✓ IPFS already initialized" -ForegroundColor Green
} else {
    try {
        Write-Host "Initializing IPFS..."
        ipfs init
        Write-Host "✓ IPFS initialized" -ForegroundColor Green
    } catch {
        Write-Host "Note: You'll need to initialize IPFS after installing it" -ForegroundColor Yellow
    }
}

Write-Host ""

# Create launch script
Write-Host "Creating launch script..."
$startScript = @'
# Collatz Network Launcher
$ipfsRunning = Get-Process -Name "ipfs" -ErrorAction SilentlyContinue

if (-not $ipfsRunning) {
    Write-Host "Starting IPFS daemon..."
    Start-Process -FilePath "ipfs" -ArgumentList "daemon" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

python network_launcher.py
'@

$startScript | Out-File -FilePath "$installDir\start.ps1" -Encoding UTF8

Write-Host "✓ Launch script created" -ForegroundColor Green
Write-Host ""

# Create desktop shortcut (optional)
$createShortcut = Read-Host "Create desktop shortcut? [Y/n]"
if ($createShortcut -ne 'n' -and $createShortcut -ne 'N') {
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Collatz Network.lnk")
    $Shortcut.TargetPath = "powershell.exe"
    $Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$installDir\start.ps1`""
    $Shortcut.WorkingDirectory = $installDir
    $Shortcut.IconLocation = "powershell.exe,0"
    $Shortcut.Description = "Collatz Distributed Verification Network"
    $Shortcut.Save()
    Write-Host "✓ Desktop shortcut created" -ForegroundColor Green
}

# Installation complete
Write-Host ""
Write-Host "=========================================="
Write-Host "  Installation Complete!"
Write-Host "=========================================="
Write-Host ""
Write-Host "To start the Collatz Network:"
Write-Host "  cd $installDir"
Write-Host "  .\start.ps1"
Write-Host ""
Write-Host "Or use the desktop shortcut if you created one."
Write-Host ""
Write-Host "Documentation:"
Write-Host "  README.md - Project overview"
Write-Host "  DISTRIBUTED_QUICKREF.md - Quick reference"
Write-Host "  DISTRIBUTED.md - Complete documentation"
Write-Host ""
