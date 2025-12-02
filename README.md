# Shrink Borders

## What It Does

This script removes uniform color borders from images and applies exactly uniform borders on all sides.

- Scans directories recursively for `.jpg`, `.jpeg`, `.png` files
- Detects uniform color borders by checking all 4 corners (must all match)
- Removes all existing borders (regardless of size or uniformity)
- Adds back exactly uniform borders of your specified width on all sides
- Saves processed images to a separate output directory
- Logs all processing decisions to a log file

The script requires all 4 corners to have the same color to detect a border. This prevents false positives like white
skies being treated as borders. It won't work with gradients or multi-colored borders.

**Key feature**: All output images will have exactly equal borders on all 4 sides, regardless of whether the input
had unequal, wonky, or missing borders.

## How to Use It

### Installation

```bash
uv sync
```

### Basic Usage

```bash
# Process images in-place (modifies originals)
uv run python shrink_borders.py /path/to/images

# Preview changes without processing (dry-run mode)
uv run python shrink_borders.py /path/to/images --dry-run

# Save to output directory (preserves originals)
uv run python shrink_borders.py /path/to/images -o processed-images

# Keep 10px border instead of default 5px
uv run python shrink_borders.py /path/to/images -p 10
```

### Options

```text
-p, --padding N       Uniform border width in pixels for all sides (default: 5)
                      Images are cropped to content, then exactly N pixels of
                      border are added to all 4 sides
-o, --output-dir D    Output directory for processed images
                      (if not specified, modifies images in-place)
-l, --log-file P      Log file path (default: shrink-borders.log)
--dry-run             Preview changes without processing files
```

### Example Output

```text
Processing: image.jpg
  Original size: 1920x1080
  Border color (4 corners match): (255, 255, 255)
  Detected borders - L:15 R:10 T:0 B:13
  Max border: 15px
  Content size: 1274x1857
  New size with uniform 5px border: 1284x1867
  Action: UNIFORM BORDERS APPLIED - Saved to processed-images/image.jpg with 5px border on all sides
```

The output shows:
- Original detected borders (which are unequal: L:15 R:10 T:0 B:13)
- The content size after removing all borders
- The final size with exactly 5px uniform borders on all sides

When corners don't match:

```text
Processing: photo-with-sky.jpg
  Original size: 1920x1080
  Action: SKIP - No uniform border detected (corners don't match)
```

### Requirements

- Python >=3.13
- Pillow (installed automatically via uv)

### Notes

- **By default, images are modified in-place** (originals overwritten)
- Use `-o` flag to save processed images to a separate directory (preserves originals)
- Images are skipped if all 4 corners don't have the same color (no uniform border detected)
- **All processed images will have exactly uniform borders** on all 4 sides equal to the padding value
- The algorithm:
  1. Detects where content starts/ends on each edge
  2. Crops to pure content (removes ALL existing borders)
  3. Adds uniform border of exactly the specified padding to all sides
- Works with unequal borders (e.g., L:15 R:10 T:0 B:13) - output will be uniform (5px on all sides)
- Always use `--dry-run` first to preview changes before processing

## Docker Usage

The tool is available as a Docker container with multi-architecture support for both Intel/AMD (TrueNAS) and Apple Silicon systems.

### Quick Start

```bash
# Pull the image
docker pull ghcr.io/johnmathews/image-borders:latest

# Process images (auto-detects output mode)
docker run --rm \
  -v "$(pwd)/images":/images:ro \
  -v "$(pwd)/output":/output \
  ghcr.io/johnmathews/image-borders:latest
```

### Configuration

The container can be configured via environment variables or command-line arguments.

#### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SHRINK_BORDERS_INPUT_DIR` | `/images` | Input directory path |
| `SHRINK_BORDERS_PADDING` | `5` | Border width in pixels |
| `SHRINK_BORDERS_OUTPUT_DIR` | (empty) | Output directory; empty means auto-detect |
| `SHRINK_BORDERS_LOG_FILE` | `/output/shrink-borders.log` | Log file path |
| `SHRINK_BORDERS_DRY_RUN` | `false` | Set to `true` for preview mode |

#### Auto-detect Behavior

The container intelligently detects your intent based on volume mounts:

- **Both `/images` and `/output` mounted**: Saves processed images to `/output`, preserves originals
- **Only `/images` mounted**: Modifies images in-place

You can override this by setting `SHRINK_BORDERS_OUTPUT_DIR` explicitly.

### Usage Examples

#### Custom padding

```bash
docker run --rm \
  -v "$(pwd)/images":/images:ro \
  -v "$(pwd)/output":/output \
  -e SHRINK_BORDERS_PADDING=10 \
  ghcr.io/johnmathews/image-borders:latest
```

#### Dry run (preview changes)

```bash
docker run --rm \
  -v "$(pwd)/images":/images \
  -e SHRINK_BORDERS_DRY_RUN=true \
  ghcr.io/johnmathews/image-borders:latest
```

#### In-place modification

```bash
docker run --rm \
  -v "$(pwd)/images":/images \
  ghcr.io/johnmathews/image-borders:latest
```

#### Direct CLI arguments

```bash
docker run --rm \
  -v "$(pwd)/photos":/data \
  ghcr.io/johnmathews/image-borders:latest \
  /data -p 10 -o /data/processed
```

### Docker Compose

Create a `docker-compose.yml`:

```yaml
services:
  shrink-borders:
    image: ghcr.io/johnmathews/image-borders:latest
    volumes:
      - ./images:/images:ro
      - ./output:/output
    environment:
      - SHRINK_BORDERS_PADDING=5
```

Run with: `docker-compose run --rm shrink-borders`

### TrueNAS Integration

The Docker image works seamlessly with TrueNAS SCALE:

1. **Add Container** in TrueNAS Apps
2. **Image**: `ghcr.io/johnmathews/image-borders:latest`
3. **Storage**:
   - Mount your photo dataset to `/images` (read-only recommended)
   - Mount output dataset to `/output`
4. **Environment Variables**: Set as needed (e.g., `SHRINK_BORDERS_PADDING=5`)
5. **Restart Policy**: `Never` (for one-off execution)
6. Run as scheduled task or manual execution

### More Information

See [DOCKER.md](DOCKER.md) for comprehensive Docker documentation including:
- Architecture details
- Building locally
- Troubleshooting
- Performance optimization
- Security considerations
- Advanced usage patterns
