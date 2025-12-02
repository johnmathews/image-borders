# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working
with code in this repository.

## Project Overview

A simple Python script to remove uniform color borders from images (.jpg,
.jpeg, .png). The script detects borders by checking all 4 corners
and crops to content while optionally preserving P pixels of border.
Designed to be tactical and straightforward - doesn't need to cover all
edge cases.

## Key Commands

```bash
# Install dependencies
uv sync

# Run the script (live mode by default)
uv run python shrink_borders.py <directory> [options]

# Test with dry run
uv run python shrink_borders.py test-images --dry-run

# Run with padding
uv run python shrink_borders.py test-images -p 10
```

## Architecture

**Single-file script** (`shrink_borders.py`) with straightforward control
flow:

1. **Border detection**: Checks all 4 corners - if they all match, uses
   that color as border reference. If corners don't match, skips the image
   (prevents false positives like white skies)
2. **Content bounds**: Scans from all four edges inward to find first
   non-border pixel
3. **Cropping logic**: Calculates crop coordinates with padding applied,
   then crops if needed
4. **Output**: Saves processed images to separate output directory
   (preserves originals)
5. **Logging**: Dual output to both console and log file showing all
   decisions

Key functions:

- `get_border_color()`: Checks all 4 corners, returns color if match or None
- `find_content_bounds()`: Core algorithm that scans from edges inward
- `process_image()`: Handles single image with logging
- `process_directory()`: Recursive directory traversal

## Important Constraints

- Borders must be single uniform color (no gradients or multi-color)
- All 4 corners must match to detect a border (prevents false positives)
- Saves to output directory (originals preserved)
- Python >=3.13 required
- Keep code simple and readable - tactical tool, not production-grade
- Use typed Python throughout
