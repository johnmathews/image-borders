# Shrink Borders

## What It Does

This script removes uniform color borders from images while preserving your specified amount of padding.

- Scans directories recursively for `.jpg`, `.jpeg`, `.png` files
- Detects uniform color borders by checking all 4 corners (must all match)
- Crops to content boundaries plus your specified padding
- Saves processed images to a separate output directory
- Logs all processing decisions to a log file

The script requires all 4 corners to have the same color to detect a border. This prevents false positives like white skies being treated as borders. It won't work with gradients or multi-colored borders.

## How to Use It

### Installation

```bash
uv sync
```

### Basic Usage

```bash
# Process images (live mode by default)
uv run python shrink_borders.py /path/to/images

# Preview changes without processing (dry-run mode)
uv run python shrink_borders.py /path/to/images --dry-run

# Keep 10px border instead of default 5px
uv run python shrink_borders.py /path/to/images -p 10

# Custom output directory
uv run python shrink_borders.py /path/to/images -o my-output
```

### Options

```text
-p, --padding N       Keep N pixels of border (default: 5)
-o, --output-dir D    Output directory for processed images
                      (default: processed-images)
-l, --log-file P      Log file path (default: shrink-borders.log)
--dry-run             Preview changes without processing files
```

### Example Output

```text
Processing: image.jpg
  Original size: 1920x1080
  Border color (4 corners match): (255, 255, 255)
  Border widths - L:200 R:200 T:100 B:100
  New size: 1520x880
  Action: CROPPED - Saved to processed-images/image.jpg with 5px border
```

Or when corners don't match:

```text
Processing: photo-with-sky.jpg
  Original size: 1920x1080
  Action: SKIP - No uniform border detected (corners don't match)
```

### Requirements

- Python >=3.13
- Pillow (installed automatically via uv)

### Notes

- Originals are preserved (processed images go to output directory)
- Images are skipped if:
  - All 4 corners don't have the same color (no uniform border detected)
  - Border is already ≤ the specified padding
  - No excess border detected
- Use `--dry-run` to test before processing
