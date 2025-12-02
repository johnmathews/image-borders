#!/usr/bin/env python3
"""Remove uniform color borders from images, keeping only P pixels of border."""

import argparse
import logging
from pathlib import Path
from typing import cast

from PIL import Image, ImageOps


def get_border_color(img: Image.Image) -> tuple[int, ...] | None:
    """
    Get the border color by checking all 4 corners.

    Returns the color if all 4 corners match, None otherwise.
    """
    width, height = img.size

    # Get all 4 corner pixels
    corners = [
        img.getpixel((0, 0)),  # top-left
        img.getpixel((width - 1, 0)),  # top-right
        img.getpixel((0, height - 1)),  # bottom-left
        img.getpixel((width - 1, height - 1)),  # bottom-right
    ]

    # Normalize each corner pixel to tuple format
    normalized_corners: list[tuple[int, ...]] = []
    for pixel in corners:
        if isinstance(pixel, (int, float)):
            normalized_corners.append((int(pixel),))
        elif pixel is None:
            normalized_corners.append((0,))
        else:
            normalized_corners.append(tuple(int(c) for c in pixel))  # type: ignore[union-attr]

    # Check if all corners match
    first_corner: tuple[int, ...] = normalized_corners[0]
    if all(corner == first_corner for corner in normalized_corners):
        return first_corner

    return None


def find_uniform_content_bounds(
    img: Image.Image, border_color: tuple[int, ...], padding: int
) -> tuple[int, int, int, int, int, int, int, int, int]:
    """
    Find the bounds of non-border content and calculate crop for uniform borders.

    Returns (left_detected, right_detected, top_detected, bottom_detected,
             content_left, content_top, content_right, content_bottom, max_border).

    The detected values show the original border widths.
    The content coordinates define the pure content area (all borders removed).
    max_border is the maximum detected border width.
    """
    width, height = img.size
    pixels = img.load()
    if pixels is None:
        return (0, 0, 0, 0, 0, 0, width, height, 0)

    # Find left boundary (detect where content starts)
    left_content = 0
    for x in range(width):
        for y in range(height):
            pixel = pixels[x, y]
            current_color = (
                (int(pixel),)
                if isinstance(pixel, (int, float))
                else tuple(int(c) for c in pixel)
            )
            if current_color != border_color:
                left_content = x
                break
        else:
            continue
        break

    # Find right boundary (detect where content ends)
    right_content = width - 1
    for x in range(width - 1, -1, -1):
        for y in range(height):
            pixel = pixels[x, y]
            current_color = (
                (int(pixel),)
                if isinstance(pixel, (int, float))
                else tuple(int(c) for c in pixel)
            )
            if current_color != border_color:
                right_content = x
                break
        else:
            continue
        break

    # Find top boundary (detect where content starts)
    top_content = 0
    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            current_color = (
                (int(pixel),)
                if isinstance(pixel, (int, float))
                else tuple(int(c) for c in pixel)
            )
            if current_color != border_color:
                top_content = y
                break
        else:
            continue
        break

    # Find bottom boundary (detect where content ends)
    bottom_content = height - 1
    for y in range(height - 1, -1, -1):
        for x in range(width):
            pixel = pixels[x, y]
            current_color = (
                (int(pixel),)
                if isinstance(pixel, (int, float))
                else tuple(int(c) for c in pixel)
            )
            if current_color != border_color:
                bottom_content = y
                break
        else:
            continue
        break

    # Calculate detected border widths
    left_border = left_content
    right_border = width - 1 - right_content
    top_border = top_content
    bottom_border = height - 1 - bottom_content

    # Find the maximum border for reporting
    max_border = max(left_border, right_border, top_border, bottom_border)

    # Return content coordinates (all borders stripped)
    # These define the pure content rectangle
    return (
        left_border,
        right_border,
        top_border,
        bottom_border,
        left_content,
        top_content,
        right_content + 1,  # +1 because crop is exclusive
        bottom_content + 1,  # +1 because crop is exclusive
        max_border,
    )


def process_image(
    file_path: Path, padding: int, output_dir: Path | None, dry_run: bool = True
) -> None:
    """Process a single image file to remove all borders and add uniform borders."""
    logger = logging.getLogger(__name__)

    try:
        with Image.open(file_path) as img:
            width, height = img.size
            border_color = get_border_color(img)

            logger.info("Processing: %s", file_path)
            logger.info("  Original size: %dx%d", width, height)

            if border_color is None:
                # No uniform border detected - add border to entire image
                logger.info("  Border color: No uniform border detected (corners don't match)")
                logger.info("  Action: Adding %dpx uniform border to entire image", padding)

                if dry_run:
                    logger.info("  Action: DRY-RUN - Would add %dpx uniform border", padding)
                    return

                # Use white as default border color for images without borders
                # Determine if image is grayscale or color
                if img.mode == 'L':
                    fill_color = 255  # White for grayscale
                elif img.mode in ('RGB', 'RGBA'):
                    fill_color = (255, 255, 255) if img.mode == 'RGB' else (255, 255, 255, 255)
                else:
                    # For other modes, convert to RGB first
                    img = img.convert('RGB')
                    fill_color = (255, 255, 255)

                # Add uniform border to entire image
                result = ImageOps.expand(img, border=padding, fill=fill_color)

                # Determine output path and save
                if output_dir:
                    output_path = output_dir / file_path.name
                else:
                    output_path = file_path

                result.save(output_path)
                logger.info(
                    "  Action: UNIFORM BORDER ADDED - Saved to %s with %dpx border on all sides",
                    output_path,
                    padding,
                )
                return

            logger.info("  Border color (4 corners match): %s", border_color)

            # Find content boundaries
            (
                left_border,
                right_border,
                top_border,
                bottom_border,
                content_left,
                content_top,
                content_right,
                content_bottom,
                max_border,
            ) = find_uniform_content_bounds(img, border_color, padding)

            logger.info(
                "  Detected borders - L:%d R:%d T:%d B:%d",
                left_border,
                right_border,
                top_border,
                bottom_border,
            )
            logger.info("  Max border: %dpx", max_border)

            # Check if there are any borders to process
            if max_border == 0 and padding == 0:
                logger.info("  Action: SKIP - No borders detected and no padding requested")
                return

            # Calculate what the content dimensions are
            content_width = content_right - content_left
            content_height = content_bottom - content_top

            # Calculate final dimensions with uniform padding
            final_width = content_width + (2 * padding)
            final_height = content_height + (2 * padding)

            logger.info("  Content size: %dx%d", content_width, content_height)
            logger.info("  New size with uniform %dpx border: %dx%d", padding, final_width, final_height)

            if dry_run:
                logger.info(
                    "  Action: DRY-RUN - Would crop to content (%d, %d, %d, %d) then add %dpx uniform border",
                    content_left,
                    content_top,
                    content_right,
                    content_bottom,
                    padding,
                )
                return

            # Step 1: Crop to pure content (remove all existing borders)
            content_only = img.crop((content_left, content_top, content_right, content_bottom))

            # Step 2: Add uniform border of exactly 'padding' pixels
            # Convert border_color tuple to proper format for expand
            if len(border_color) == 1:
                fill_color = border_color[0]
            else:
                fill_color = border_color

            result = ImageOps.expand(content_only, border=padding, fill=fill_color)

            # Determine output path and save
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / file_path.name
            else:
                output_path = file_path

            result.save(output_path)

            if output_dir:
                logger.info(
                    "  Action: UNIFORM BORDERS APPLIED - Saved to %s with %dpx border on all sides",
                    output_path,
                    padding,
                )
            else:
                logger.info(
                    "  Action: UNIFORM BORDERS APPLIED - Modified in-place with %dpx border on all sides",
                    padding,
                )

    except Exception as e:
        logger.error("  Error processing %s: %s", file_path, e)


def process_directory(
    directory: Path, padding: int, output_dir: Path | None, dry_run: bool = True
) -> None:
    """Recursively process all images in a directory."""
    logger = logging.getLogger(__name__)

    logger.info("\n%s", "=" * 80)
    logger.info("Scanning directory: %s", directory)
    logger.info("%s", "=" * 80)

    # Find all image files
    image_extensions = {".jpg", ".jpeg", ".png"}
    image_files = [
        f
        for f in directory.rglob("*")
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
        default=5,
        help="Uniform border width in pixels for all sides (default: 5). Images will be cropped or expanded to achieve exactly this border width on all edges.",
    )
    _ = parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for processed images (if not specified, modifies images in-place)",
    )
    _ = parser.add_argument(
        "-l",
        "--log-file",
        type=Path,
        default=Path("shrink-borders.log"),
        help="Path to log file (default: shrink-borders.log)",
    )
    _ = parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without processing files (default is live mode)",
    )

    args = parser.parse_args()

    # Extract typed values from argparse namespace
    dry_run: bool = cast(bool, args.dry_run)
    directory: Path = cast(Path, args.directory)
    padding: int = cast(int, args.padding)
    output_dir: Path | None = cast(Path | None, args.output_dir)
    log_file: Path = cast(Path, args.log_file)

    if not directory.exists():
        print(f"Error: Directory '{directory}' does not exist")
        return

    if not directory.is_dir():
        print(f"Error: '{directory}' is not a directory")
        return

    setup_logging(log_file)
    logger = logging.getLogger(__name__)

    logger.info("%s", "=" * 80)
    logger.info("SHRINK BORDERS - Image Border Removal Tool")
    logger.info("%s", "=" * 80)
    logger.info("Directory: %s", directory)
    logger.info("Padding: %d pixels", padding)
    if output_dir:
        logger.info("Output directory: %s", output_dir)
    else:
        logger.info("Output: In-place modification")
    logger.info("Log file: %s", log_file)
    logger.info("Mode: %s", "DRY-RUN" if dry_run else "LIVE")
    logger.info("%s", "=" * 80)

    process_directory(directory, padding, output_dir, dry_run)

    logger.info("\n%s", "=" * 80)
    logger.info("Processing complete!")
    logger.info("Log saved to: %s", log_file)
    if not dry_run:
        if output_dir:
            logger.info("Processed images saved to: %s", output_dir)
        else:
            logger.info("Images modified in-place")
    logger.info("%s", "=" * 80)


if __name__ == "__main__":
    main()
