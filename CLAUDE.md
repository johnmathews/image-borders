# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working
with code in this repository.

## Project Overview

A simple Python script to remove uniform color borders from images (.jpg,
.jpeg, .png) and apply exactly uniform borders on all sides. The script
detects borders by checking all 4 corners, crops to pure content, then
adds exactly P pixels of uniform border on all sides. Designed to be
tactical and straightforward - doesn't need to cover all edge cases.

## Key Commands

```bash
# Install dependencies
uv sync

# Run the script in-place (modifies originals)
uv run python shrink_borders.py <directory>

# Test with dry run
uv run python shrink_borders.py test-images --dry-run

# Save to output directory (preserves originals)
uv run python shrink_borders.py test-images -o processed-images

# Run with padding
uv run python shrink_borders.py test-images -p 10
```

## Architecture

**Single-file script** (`shrink_borders.py`) with straightforward control
flow:

1. **Border detection**: Checks all 4 corners - if they all match, uses
   that color as border reference. If corners don't match, adds white border
   to entire image without removing content
2. **Content bounds** (for images with uniform borders): Scans from all four
   edges inward to find first non-border pixel on each edge
3. **Uniform border application**:
   - **With uniform border detected**: Two-step process - crop to pure content
     (removes ALL existing borders), then add uniform border of exactly P pixels
     to all 4 sides using ImageOps.expand()
   - **No uniform border detected**: Add white border directly to entire image
4. **Output**: By default modifies images in-place. If `-o` flag provided,
   saves to separate output directory (preserves originals)
5. **Logging**: Dual output to both console and log file showing detected
   borders, content size, and final dimensions

Key functions:

- `get_border_color()`: Checks all 4 corners, returns color if match or None
- `find_uniform_content_bounds()`: Scans from edges inward to find content boundaries,
  returns detected border widths and content crop coordinates
- `process_image()`: Crops to content then adds uniform borders using ImageOps.expand()
- `process_directory()`: Recursive directory traversal

## Important Constraints

- For border removal: Borders must be single uniform color (no gradients or multi-color)
- All 4 corners must match to detect a border - if they don't match, white border is added
- Default behavior modifies images in-place (use `-o` to preserve originals)
- **All output images have exactly uniform borders on all 4 sides**
- Works with any input border configuration (unequal, wonky, missing, or none)
- Python >=3.13 required
- Keep code simple and readable - tactical tool, not production-grade
- Use typed Python throughout
