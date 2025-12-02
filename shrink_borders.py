#!/usr/bin/env python3
"""Remove uniform color borders from images, keeping only P pixels of border."""

import argparse
import logging
from pathlib import Path

from PIL import Image


def get_border_color(img: Image.Image) -> tuple[int, ...]:
    """Get the border color from the top-left corner pixel."""
    pixel = img.getpixel((0, 0))
    if isinstance(pixel, (int, float)):
        return (int(pixel),)
    if pixel is None:
        return (0,)
    return tuple(int(c) for c in pixel)  # type: ignore[union-attr]


def find_content_bounds(
    img: Image.Image, border_color: tuple[int, ...], padding: int
) -> tuple[int, int, int, int]:
    """
    Find the bounds of non-border content.

    Returns (left, top, right, bottom) coordinates with padding applied.
    """
    width, height = img.size
    pixels = img.load()
    if pixels is None:
        return (0, 0, width, height)

    # Find left boundary
    left = 0
    for x in range(width):
        for y in range(height):
            pixel = pixels[x, y]
            current_color = (int(pixel),) if isinstance(pixel, (int, float)) else tuple(int(c) for c in pixel)
            if current_color != border_color:
                left = max(0, x - padding)
                break
        else:
            continue
        break

    # Find right boundary
    right = width
    for x in range(width - 1, -1, -1):
        for y in range(height):
            pixel = pixels[x, y]
            current_color = (int(pixel),) if isinstance(pixel, (int, float)) else tuple(int(c) for c in pixel)
            if current_color != border_color:
                right = min(width, x + 1 + padding)
                break
        else:
            continue
        break

    # Find top boundary
    top = 0
    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            current_color = (int(pixel),) if isinstance(pixel, (int, float)) else tuple(int(c) for c in pixel)
            if current_color != border_color:
                top = max(0, y - padding)
                break
        else:
            continue
        break

    # Find bottom boundary
    bottom = height
    for y in range(height - 1, -1, -1):
        for x in range(width):
            pixel = pixels[x, y]
            current_color = (int(pixel),) if isinstance(pixel, (int, float)) else tuple(int(c) for c in pixel)
            if current_color != border_color:
                bottom = min(height, y + 1 + padding)
                break
        else:
            continue
        break

    return (left, top, right, bottom)


def process_image(
    file_path: Path, padding: int, output_dir: Path, dry_run: bool = True
) -> None:
    """Process a single image file to remove excess borders."""
    logger = logging.getLogger(__name__)

    try:
        with Image.open(file_path) as img:
            width, height = img.size
            border_color = get_border_color(img)

            logger.info("Processing: %s", file_path)
            logger.info("  Original size: %dx%d", width, height)
            logger.info("  Border color: %s", border_color)

            # Find content boundaries
            left, top, right, bottom = find_content_bounds(img, border_color, padding)

            # Check if cropping is needed
            if left == 0 and top == 0 and right == width and bottom == height:
                logger.info("  Action: SKIP - No excess border detected")
                return

            crop_width = right - left
            crop_height = bottom - top

            # Calculate border widths
            left_border = left
            right_border = width - right
            top_border = top
            bottom_border = height - bottom

            logger.info("  Border widths - L:%d R:%d T:%d B:%d", left_border, right_border, top_border, bottom_border)
            logger.info("  New size: %dx%d", crop_width, crop_height)

            if dry_run:
                logger.info("  Action: DRY-RUN - Would crop to (%d, %d, %d, %d)", left, top, right, bottom)
                return

            # Create output directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)

            # Determine output path
            output_path = output_dir / file_path.name

            # Crop and save
            cropped = img.crop((left, top, right, bottom))
            cropped.save(output_path)
            logger.info("  Action: CROPPED - Saved to %s with %dpx border", output_path, padding)

    except Exception as e:
        logger.error("  Error processing %s: %s", file_path, e)


def process_directory(
    directory: Path, padding: int, output_dir: Path, dry_run: bool = True
) -> None:
    """Recursively process all images in a directory."""
    logger = logging.getLogger(__name__)

    logger.info("\n%s", "="*80)
    logger.info("Scanning directory: %s", directory)
    logger.info("%s", "="*80)

    # Find all image files
    image_extensions = {".jpg", ".jpeg", ".png"}
    image_files = [
        f for f in directory.rglob("*")
        if f.is_file() and f.suffix.lower() in image_extensions
    ]

    if not image_files:
        logger.info("No image files found in %s", directory)
        return

    logger.info("Found %d image(s)", len(image_files))

    for image_file in sorted(image_files):
        process_image(image_file, padding, output_dir, dry_run)


def setup_logging(log_file: Path) -> None:
    """Configure logging to both file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[
            logging.FileHandler(log_file, mode="w"),
            logging.StreamHandler(),
        ],
    )


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Remove uniform color borders from images, keeping only P pixels of border."
    )
    _ = parser.add_argument(
        "directory",
        type=Path,
        help="Directory to process (will scan recursively)",
    )
    _ = parser.add_argument(
        "-p",
        "--padding",
        type=int,
        default=50,
        help="Number of border pixels to keep (default: 50)",
    )
    _ = parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("processed-images"),
        help="Output directory for processed images (default: processed-images)",
    )
    _ = parser.add_argument(
        "-l",
        "--log-file",
        type=Path,
        default=Path("shrink-borders.log"),
        help="Path to log file (default: shrink-borders.log)",
    )
    _ = parser.add_argument(
        "--no-dry-run",
        action="store_true",
        help="Actually process files (default is dry-run mode)",
    )

    args = parser.parse_args()

    # Invert the logic: dry_run is True by default unless --no-dry-run is specified
    no_dry_run = bool(args.no_dry_run)
    dry_run = not no_dry_run

    directory = args.directory if isinstance(args.directory, Path) else Path(str(args.directory))
    padding = args.padding if isinstance(args.padding, int) else int(args.padding)
    output_dir = args.output_dir if isinstance(args.output_dir, Path) else Path(str(args.output_dir))
    log_file = args.log_file if isinstance(args.log_file, Path) else Path(str(args.log_file))

    if not directory.exists():
        print(f"Error: Directory '{directory}' does not exist")
        return

    if not directory.is_dir():
        print(f"Error: '{directory}' is not a directory")
        return

    setup_logging(log_file)
    logger = logging.getLogger(__name__)

    logger.info("%s", "="*80)
    logger.info("SHRINK BORDERS - Image Border Removal Tool")
    logger.info("%s", "="*80)
    logger.info("Directory: %s", directory)
    logger.info("Padding: %d pixels", padding)
    logger.info("Output directory: %s", output_dir)
    logger.info("Log file: %s", log_file)
    logger.info("Mode: %s", "DRY-RUN" if dry_run else "LIVE")
    logger.info("%s", "="*80)

    process_directory(directory, padding, output_dir, dry_run)

    logger.info("\n%s", "="*80)
    logger.info("Processing complete!")
    logger.info("Log saved to: %s", log_file)
    if not dry_run:
        logger.info("Processed images saved to: %s", output_dir)
    logger.info("%s", "="*80)


if __name__ == "__main__":
    main()
