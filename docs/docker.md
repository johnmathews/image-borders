# Docker Guide

Complete guide for running shrink-borders in Docker.

## Quick Start

```bash
# Pull the image
docker pull ghcr.io/johnmathews/image-borders:latest

# Process images with auto-detect (saves to /output if mounted)
docker run --rm \
  -v "$(pwd)/images":/images:ro \
  -v "$(pwd)/output":/output \
  ghcr.io/johnmathews/image-borders:latest
```

## Architecture

The Docker image is built as a multi-stage, multi-architecture container:

- **Architectures**: linux/amd64 (Intel/AMD), linux/arm64 (Apple Silicon)
- **Base**: Python 3.13-slim
- **Size**: ~150MB uncompressed (~50MB compressed)
- **Security**: Runs as non-root user (UID 1000)
- **Registry**: GitHub Container Registry (ghcr.io)

### Build Strategy

Multi-stage build optimizes for size and security:

1. **Builder stage**: Installs dependencies using `uv` in virtual environment
2. **Runtime stage**: Copies only necessary files, runs as non-root user

## Volume Mounts

The container expects two volume mounts:

| Mount Point | Purpose                                        | Required   |
| ----------- | ---------------------------------------------- | ---------- |
| `/images`   | Input directory to scan for images             | Yes        |
| `/output`   | Output directory for processed images and logs | Optional\* |

\*If `/output` is not mounted, images are modified in-place in `/images`.

### Auto-detect Behavior

The container intelligently detects your intent:

- **Both volumes mounted** (`/images` + `/output`): Saves processed images to `/output`, preserves originals
- **Only `/images` mounted**: Modifies images in-place (matches CLI default behavior)
- **Override**: Set `SHRINK_BORDERS_OUTPUT_DIR` environment variable to force specific behavior

## Configuration

### Environment Variables

| Variable                    | Default                      | Description                                  |
| --------------------------- | ---------------------------- | -------------------------------------------- |
| `SHRINK_BORDERS_INPUT_DIR`  | `/images`                    | Input directory path                         |
| `SHRINK_BORDERS_PADDING`    | `5`                          | Border width in pixels                       |
| `SHRINK_BORDERS_OUTPUT_DIR` | (empty)                      | Output directory; empty triggers auto-detect |
| `SHRINK_BORDERS_LOG_FILE`   | `/output/shrink-borders.log` | Log file path                                |
| `SHRINK_BORDERS_DRY_RUN`    | `false`                      | Set to `true` for preview mode               |

### Configuration Methods

#### 1. Environment Variables (Recommended)

```bash
docker run --rm \
  -v "$(pwd)/in":/images:ro \
  -v "$(pwd)/out":/output \
  -e SHRINK_BORDERS_PADDING=10 \
  -e SHRINK_BORDERS_DRY_RUN=false \
  ghcr.io/johnmathews/image-borders:latest
```

#### 2. Command-Line Arguments

Environment variables are ignored when CLI arguments are provided:

```bash
docker run --rm \
  -v "$(pwd)/in":/data \
  ghcr.io/johnmathews/image-borders:latest \
  /data -p 10 -o /data/processed --dry-run
```

## Usage Patterns

### Development/Testing

Use docker-compose for quick iteration:

```yaml
# docker-compose.yml
services:
 shrink-borders:
  build: .
  volumes:
   - ./test-images:/images:ro
   - ./output:/output
  environment:
   - SHRINK_BORDERS_PADDING=5
```

```bash
# Build and run
docker-compose build
docker-compose run --rm shrink-borders

# With custom settings
docker-compose run --rm \
  -e SHRINK_BORDERS_PADDING=15 \
  -e SHRINK_BORDERS_DRY_RUN=true \
  shrink-borders
```

### Production Deployment

Pull from registry and run:

```bash
docker pull ghcr.io/johnmathews/image-borders:latest

docker run --rm \
  -v /data/photos:/images:ro \
  -v /data/processed:/output \
  ghcr.io/johnmathews/image-borders:latest
```

### TrueNAS SCALE

Configure container in TrueNAS web UI:

**Container Settings:**

- Image Repository: `ghcr.io/johnmathews/image-borders`
- Image Tag: `latest`
- Restart Policy: `Never` (one-off execution)

**Storage (Host Path Volumes):**

- `/mnt/pool/photos` → `/images` (Mount Path), Read Only: ✓
- `/mnt/pool/processed` → `/output` (Mount Path)

**Environment Variables:**

- `SHRINK_BORDERS_PADDING`: `5`
- `SHRINK_BORDERS_DRY_RUN`: `false`

**Execution:**

- Run as scheduled task via TrueNAS cron or manual execution
- View logs in TrueNAS UI or via `docker logs`

### Scheduled Execution

Create a systemd timer or cron job:

```bash
#!/bin/bash
# /usr/local/bin/process-images.sh

docker run --rm \
  -v /data/photos:/images:ro \
  -v /data/processed:/output \
  -e SHRINK_BORDERS_PADDING=5 \
  ghcr.io/johnmathews/image-borders:latest
```

Cron schedule (daily at 2 AM):

```cron
0 2 * * * /usr/local/bin/process-images.sh >> /var/log/shrink-borders.log 2>&1
```

## Examples

### Basic Usage (Auto-detect)

```bash
docker run --rm \
  -v "$(pwd)/images":/images:ro \
  -v "$(pwd)/output":/output \
  ghcr.io/johnmathews/image-borders:latest
```

Auto-detects both volumes and saves to `/output`.

### In-place Modification

```bash
docker run --rm \
  -v "$(pwd)/images":/images \
  ghcr.io/johnmathews/image-borders:latest
```

Only `/images` mounted, so images are modified in-place.

### Custom Padding

```bash
docker run --rm \
  -v "$(pwd)/images":/images:ro \
  -v "$(pwd)/output":/output \
  -e SHRINK_BORDERS_PADDING=15 \
  ghcr.io/johnmathews/image-borders:latest
```

### Dry Run (Preview)

```bash
docker run --rm \
  -v "$(pwd)/images":/images \
  -e SHRINK_BORDERS_DRY_RUN=true \
  ghcr.io/johnmathews/image-borders:latest
```

Preview changes without modifying files.

### Direct CLI Arguments

```bash
docker run --rm \
  -v "$(pwd)/photos":/data \
  ghcr.io/johnmathews/image-borders:latest \
  /data -p 10 -o /data/processed --log-file /data/log.txt
```

Bypasses environment variables entirely.

### Help

```bash
docker run --rm ghcr.io/johnmathews/image-borders:latest --help
```

## Building Locally

### Single Platform

```bash
# Build for your current platform
docker build -t shrink-borders:local .

# Test
docker run --rm shrink-borders:local --help
```

### Multi-Platform

```bash
# Create builder
docker buildx create --use

# Build for both architectures
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t shrink-borders:multi \
  --load .
```

## Logging

The container provides dual logging:

1. **stdout/stderr**: Visible via `docker logs`
2. **Log file**: Written to `/output/shrink-borders.log` (if `/output` mounted)

### Viewing Logs

```bash
# Container logs (stdout)
docker logs <container-id>

# Log file (if /output mounted)
cat output/shrink-borders.log
```

### Log File Location

Default: `/output/shrink-borders.log`

Override with:

```bash
-e SHRINK_BORDERS_LOG_FILE=/custom/path/log.txt
```

## Troubleshooting

### Permission Issues

The container runs as UID 1000. To match your host user:

```bash
docker run --rm \
  --user $(id -u):$(id -g) \
  -v "$(pwd)":/images \
  ghcr.io/johnmathews/image-borders:latest
```

Or set ownership on host:

```bash
sudo chown -R 1000:1000 images/ output/
```

### Image Not Found

If pulling from ghcr.io fails:

```bash
# Authenticate (if package is private)
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Pull
docker pull ghcr.io/johnmathews/image-borders:latest
```

### No Images Processed

Check:

1. Images are in mounted directory: `docker run ... ls /images`
2. Supported formats: `.jpg`, `.jpeg`, `.png`
3. Corner pixels match (4 corners must be same color)

Enable dry-run to see detection details:

```bash
-e SHRINK_BORDERS_DRY_RUN=true
```

### Container Exits Immediately

Check logs:

```bash
docker logs <container-id>
```

Common causes:

- Invalid directory path in CLI arguments
- Permissions on mounted volumes
- Missing required arguments

### Wrong Architecture

Verify platform:

```bash
docker inspect ghcr.io/johnmathews/image-borders:latest | grep Architecture
```

Should show:

- `amd64` on Intel/AMD systems
- `arm64` on Apple Silicon

## Performance

Container overhead is minimal (~10ms). Performance matches native execution.

**Benchmarks:**

- 100 images (1920×1080): ~45 seconds
- ARM64 and AMD64: Similar performance

**Optimization:**

- Use read-only mounts (`:ro`) for input to prevent accidental modification
- Mount `/output` on fast storage for better I/O
- Consider tmpfs for logs if persistence not needed:
  ```bash
  --tmpfs /output
  ```

## CI/CD

Images are automatically built and pushed to ghcr.io via GitHub Actions.

**Triggers:**

- Push to `main`: Builds and pushes `latest` tag
- Version tags (`v*`): Builds and pushes semantic version tags
- Pull requests: Builds for validation (no push)

**Available Tags:**

- `latest`: Most recent main branch build
- `main-<sha>`: Specific commit from main
- `v1.2.3`, `v1.2`, `v1`: Semantic version tags

**Example:**

```bash
# Latest stable
docker pull ghcr.io/johnmathews/image-borders:latest

# Specific version
docker pull ghcr.io/johnmathews/image-borders:v1.0.0

# Specific commit
docker pull ghcr.io/johnmathews/image-borders:main-abc1234
```

## Advanced Usage

### Custom Base Image

Edit Dockerfile to use different Python version:

```dockerfile
FROM python:3.12-slim AS builder
```

### Resource Limits

Limit CPU and memory:

```bash
docker run --rm \
  --cpus="2.0" \
  --memory="512m" \
  -v "$(pwd)/images":/images \
  ghcr.io/johnmathews/image-borders:latest
```

### Network Isolation

Container doesn't need network access:

```bash
docker run --rm \
  --network none \
  -v "$(pwd)/images":/images \
  ghcr.io/johnmathews/image-borders:latest
```

## Security

### Container Security

- ✅ Runs as non-root user (UID 1000)
- ✅ Minimal attack surface (slim base, no shell utilities)
- ✅ No network access required
- ✅ Read-only root filesystem compatible
- ✅ No secrets or credentials required

### Read-only Root Filesystem

```bash
docker run --rm \
  --read-only \
  --tmpfs /tmp \
  -v "$(pwd)/images":/images \
  -v "$(pwd)/output":/output \
  ghcr.io/johnmathews/image-borders:latest
```

### Security Scanning

Images are automatically scanned by GitHub for vulnerabilities.

Manual scan:

```bash
docker scan ghcr.io/johnmathews/image-borders:latest
```

## Support

For issues, questions, or contributions:

- GitHub Issues: https://github.com/johnmathews/image-borders/issues
- Documentation: https://github.com/johnmathews/image-borders
