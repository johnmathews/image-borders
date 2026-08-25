# Shrink Borders

## What It Does

This script removes uniform color borders from images and applies exactly uniform borders on all sides.

- Scans directories recursively for `.jpg`, `.jpeg`, `.png` files
- Detects uniform color borders by checking all 4 corners
- **If borders detected**: Removes all existing borders and adds back uniform borders
- **If no borders detected**: Adds uniform borders to the entire image (using white)
- Modifies images in-place by default, or saves them to a separate output directory with `-o`
- Logs all processing decisions to the console and a log file

**Key feature**: All output images will have exactly equal borders on all 4 sides, regardless of whether the input
had unequal, wonky, missing, or no borders at all.

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
usage: shrink_borders.py [-h] [-p PADDING] [-o OUTPUT_DIR] [-l LOG_FILE] [--dry-run] directory

positional arguments:
  directory             Directory to process (will scan recursively)

options:
  -h, --help            show this help message and exit
  -p, --padding PADDING
                        Uniform border width in pixels for all sides (default: 5). Images will be
                        cropped or expanded to achieve exactly this border width on all edges.
  -o, --output-dir OUTPUT_DIR
                        Output directory for processed images (if not specified, modifies images in-place)
  -l, --log-file LOG_FILE
                        Path to log file (default: shrink-borders.log)
  --dry-run             Preview changes without processing files (default is live mode)
```

See [docs/how-it-works.md](docs/how-it-works.md) for the detection algorithm and output layout in detail.

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

When no uniform border is detected (corners don't match):

```text
Processing: photo-with-sky.jpg
  Original size: 1920x1080
  Border color: No uniform border detected (corners don't match)
  Action: Adding 5px uniform border to entire image
  Action: UNIFORM BORDER ADDED - Saved to processed-images/photo-with-sky.jpg with 5px border on all sides
```

In this case, a white border is added around the entire image without removing anything.

### Requirements

- Python >=3.13
- Pillow (installed automatically via uv)

### Notes

- **By default, images are modified in-place** (originals overwritten)
- Use `-o` flag to save processed images to a separate directory (preserves originals). Output is flat:
  `OUTPUT_DIR/<file name>`, input sub-directories are not recreated
- **All processed images will have exactly uniform borders** on all 4 sides equal to the padding value
- The algorithm for images WITH uniform borders:
  1. Detects where content starts/ends on each edge
  2. Crops to pure content (removes ALL existing borders)
  3. Adds uniform border of exactly the specified padding to all sides
- For images WITHOUT uniform borders (corners don't match):
  - Adds a white border around the entire image
  - No content is removed
- Works with unequal borders (e.g., L:15 R:10 T:0 B:13) - output will be uniform (5px on all sides)
- Always use `--dry-run` first to preview changes before processing

## Development

```bash
uv sync                          # runtime + dev dependencies
uv run python -m pytest          # tests
uv run python -m pytest --cov    # tests with coverage
uv run ruff check .              # lint
uv run ruff format .             # format
uv run pyright                   # type check
```

Tests live in `tests/` and build their images with Pillow at run time, so there are no image fixtures to maintain.
CI (`.github/workflows/test.yml`) runs the same three commands on every push and pull request.

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

See [docs/docker.md](docs/docker.md) for comprehensive Docker documentation including:
- Architecture details
- Building locally
- Troubleshooting
- Performance optimization
- Security considerations
- Advanced usage patterns
