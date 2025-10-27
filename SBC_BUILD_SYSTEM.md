# Automated SBC Image Building System

This document describes the automated build system for creating ready-to-use Single Board Computer (SBC) images with Collatz Network pre-installed.

## Overview

The build system uses **GitHub Actions** to automatically create multi-platform SBC images whenever:
- A new release tag is created (e.g., `v1.0.0`)
- Code is pushed to the master branch
- Manual workflow dispatch is triggered

## Supported Platforms

| Platform | Target Devices | Architecture | Base OS |
|----------|----------------|--------------|---------|
| `rpi4-arm64` | Raspberry Pi 4, 400, CM4 | 64-bit ARM | Raspberry Pi OS Lite |
| `rpi4-arm32` | Raspberry Pi 4, 400, CM4 | 32-bit ARM | Raspberry Pi OS Lite |
| `rpi3-arm64` | Raspberry Pi 3, 3A+, 3B+ | 64-bit ARM | Raspberry Pi OS Lite |
| `rpi3-arm32` | Raspberry Pi 3, 3A+, 3B+ | 32-bit ARM | Raspberry Pi OS Lite |
| `rpi-zero2` | Raspberry Pi Zero 2 W | 64-bit ARM | Raspberry Pi OS Lite |
| `rpi-legacy` | Raspberry Pi 1, 2, Zero | 32-bit ARM | Raspberry Pi OS Lite |
| `ubuntu-arm64` | Orange Pi, Rock Pi, Odroid (newer) | 64-bit ARM | Ubuntu Server 22.04 |
| `ubuntu-arm32` | Orange Pi, Rock Pi (older models) | 32-bit ARM | Ubuntu Server 22.04 |

## Workflows

### 1. Main Build Workflow (`.github/workflows/build-sbc-images.yml`)

**Triggers:**
- Tag creation (`v*`)
- Push to master branch
- Manual dispatch

**Process:**
1. **Setup Job**: Determines platforms to build and version info
2. **Build Job Matrix**: Parallel builds for each platform
   - Downloads base OS image
   - Mounts and modifies filesystem
   - Installs Collatz Network and dependencies
   - Creates systemd services
   - Compresses final image
   - Generates SHA256 checksums
3. **Release Job**: Creates GitHub release with all built images
4. **Summary Job**: Reports build status

### 2. Test Workflow (`.github/workflows/test-build.yml`)

**Triggers:**
- Pull requests affecting build scripts
- Manual dispatch

**Process:**
- Validates shell script syntax
- Tests build script help output
- Verifies environment setup
- Quick validation without full image builds

### 3. Download Links Updater (`.github/workflows/update-downloads.yml`)

**Triggers:**
- New release published

**Process:**
- Updates README.md with download links for latest release
- Creates device compatibility table
- Adds installation instructions
- Commits changes back to repository

### 4. Status Badge Generator (`.github/workflows/badge.yml`)

**Triggers:**
- Build workflow completion

**Process:**
- Generates build status badge
- Updates badge in README

## Build Process Details

### Image Creation Steps

1. **Base Image Download**
   - Downloads official Raspberry Pi OS or Ubuntu images
   - Verifies and extracts compressed images

2. **Image Preparation**
   - Copies base image to working copy
   - Expands image size (+1GB for Collatz files)
   - Creates loop device and mounts partitions

3. **System Modification**
   - Enables SSH by default
   - Creates Wi-Fi configuration template
   - Sets up user directories (pi/ubuntu)

4. **Collatz Installation**
   - Clones Collatz Network source code
   - Creates dependency installation script
   - Sets up systemd service for auto-start
   - Creates first-boot setup script
   - Adds user documentation

5. **Finalization**
   - Unmounts filesystems
   - Compresses image with xz
   - Generates SHA256 checksums
   - Uploads as GitHub artifacts

### First Boot Process

Images are designed for zero-configuration deployment:

1. **Boot**: Device boots from flashed SD card
2. **Auto-Setup**: `/etc/rc.local` runs setup script
3. **Dependencies**: Installs Python packages and IPFS
4. **Configuration**: Initializes IPFS and sets up services
5. **Ready**: User can SSH in and run Collatz Network

## Manual Workflow Dispatch

You can trigger builds manually via GitHub web interface:

1. Go to **Actions** tab in GitHub repository
2. Select **Build Multi-Platform SBC Images**
3. Click **Run workflow**
4. Choose options:
   - **Platforms**: `all` or comma-separated list (e.g., `rpi4-arm64,ubuntu-arm64`)
   - **Create Release**: Whether to create GitHub release

## Local Testing

Use the validation script to test before pushing:

```bash
chmod +x validate-workflows.sh
./validate-workflows.sh
```

This checks:
- YAML syntax validation
- Shell script linting
- Platform configuration
- README integration

## Build Artifacts

Each successful build produces:

### Per-Platform Artifacts
- `collatz-network-<platform>-<version>.img.xz` - Compressed disk image
- `collatz-network-<platform>-<version>.img.xz.sha256` - Checksum file

### Release Assets (for tagged builds)
- All platform images and checksums
- `ALL-CHECKSUMS.sha256` - Combined checksum file
- `INSTALLATION-GUIDE.md` - Complete setup instructions

## File Sizes

Typical compressed image sizes:
- **Raspberry Pi OS**: ~400-500MB
- **Ubuntu Server**: ~600-800MB

Uncompressed images are ~4GB (expandable on first boot).

## Security Considerations

### Build Environment
- Runs in clean Ubuntu containers
- Uses official base images from Raspberry Pi Foundation and Ubuntu
- All downloads verified with checksums where available

### Image Security
- SSH enabled but requires key-based or password authentication
- Default passwords should be changed on first login
- Firewall not enabled by default (user configurable)
- Auto-update disabled (manual `git pull` recommended)

### Checksums
- SHA256 checksums provided for all images
- Users should verify downloads before flashing

## Troubleshooting

### Build Failures

**Common Issues:**
- Insufficient disk space (builds need ~8GB free)
- Network timeouts downloading base images
- Architecture mismatch in cross-compilation

**Solutions:**
- Check GitHub Actions logs for specific errors
- Free disk space in workflow
- Retry failed builds
- Test locally with Docker if needed

### Image Issues

**Boot Problems:**
- Verify checksum of downloaded image
- Ensure complete flash (not interrupted)
- Check SD card health
- Verify power supply adequacy

**Network Issues:**
- Configure Wi-Fi in `/boot/wpa_supplicant.conf`
- Check network connectivity
- Verify SSH keys/passwords

## Development Workflow

### Adding New Platforms

1. Update platform arrays in `build-pi-image.sh`:
   ```bash
   declare -A PLATFORMS=(
       ["new-platform"]="base-image-name"
       # ... existing platforms
   )
   ```

2. Add download URLs:
   ```bash
   declare -A DOWNLOAD_URLS=(
       ["new-platform"]="https://example.com/base-image-url/"
       # ... existing URLs
   )
   ```

3. Test locally with Docker
4. Update documentation and README

### Modifying Build Process

1. Edit `build-pi-image.sh` for build logic changes
2. Update workflows in `.github/workflows/` for CI changes
3. Test with validation script
4. Submit PR for review

### Release Process

1. Test builds work correctly
2. Create and push version tag: `git tag v1.0.0 && git push origin v1.0.0`
3. Workflow automatically builds all platforms
4. Review and publish GitHub release
5. Download links automatically update in README

## Monitoring

### Build Status
- GitHub Actions tab shows workflow status
- README badge shows current build status
- Email notifications for failed builds (if configured)

### Metrics
- Build duration typically 30-60 minutes for all platforms
- Parallel builds reduce total time
- Artifact retention: 30 days for development builds, permanent for releases

## Future Enhancements

### Planned Features
- **Incremental builds**: Only rebuild changed platforms
- **Multi-arch Docker**: Native ARM builds for faster compilation
- **Additional platforms**: RISC-V, x86 SBCs
- **Custom configurations**: User-selectable build options
- **Testing automation**: Boot tests in QEMU

### Infrastructure Improvements
- **Build caching**: Reuse base images and dependencies
- **Distributed builds**: Multiple runners for faster builds
- **Quality gates**: Automated testing before release
- **Metrics collection**: Build performance tracking