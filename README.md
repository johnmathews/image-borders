# Shrink Borders

Remove uniform color borders from images, keeping only P pixels.

## Quick Start

```bash
# Install
uv sync

# Dry run (default, preview without changes)
uv run python shrink_borders.py /path/to/images

# Actually process files with 50px border (default)
uv run python shrink_borders.py /path/to/images --no-dry-run

# Keep 10px border instead
uv run python shrink_borders.py /path/to/images -p 10 --no-dry-run

# Custom output directory
uv run python shrink_borders.py /path/to/images -o my-output --no-dry-run
```

## What It Does

- Scans directory recursively for `.jpg`, `.jpeg`, `.png` files
- Detects uniform color borders (assumes top-left pixel is border color)
- Crops to content + padding pixels
- Saves processed images to output directory (default: `processed-images/`)
- Runs in dry-run mode by default (safe to test first!)
- Logs all actions to `shrink-borders.log`

## Options

```text
-p, --padding N       Keep N pixels of border (default: 50)
-o, --output-dir D    Output directory for processed images
                      (default: processed-images)
-l, --log-file P      Log file path (default: shrink-borders.log)
--no-dry-run          Actually process files (default is dry-run mode)
```

## Requirements

- Python >=3.13
- Pillow (installed automatically via uv)

## Example Output

```text
Processing: image.jpg
  Original size: 1920x1080
  Border color: (255, 255, 255)
  Border widths - L:200 R:200 T:100 B:100
  New size: 1520x880
  Action: CROPPED - Saved to processed-images/image.jpg with 50px border
```

## Notes

- Assumes borders are single uniform color
- Uses top-left pixel to determine border color
- Saves to separate output directory (originals are preserved!)
- Skips files with no excess border
- Default dry-run mode is safe for testing
