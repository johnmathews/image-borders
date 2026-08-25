# How It Works

`shrink_borders.py` is a single-file Pillow script. It walks a directory, and for every image it either
**strips all existing borders and re-adds equal ones**, or, when it cannot identify a border colour, **adds a white
border around the whole image**. Either way, every output image ends up with exactly `padding` pixels of border on
all four sides.

## Detection algorithm

1. **Border colour** (`get_border_color`): read the four corner pixels. If all four are the same colour, that colour
   is the border colour. If any corner differs, the image is treated as having no uniform border.
2. **Content bounds** (`find_uniform_content_bounds`): with a border colour known, scan inward from each edge (left,
   right, top, bottom) until a column/row contains a pixel that is not the border colour. That gives the detected
   border width on each side and the bounding box of the content. The scan is exact-match: any pixel that is not
   _identical_ to the corner colour counts as content, so JPEG compression noise near a border can make it read as
   content.
3. **Rebuild** (`process_image`):
   - Border colour found: crop to the content box (all borders removed, however unequal), then
     `ImageOps.expand` it by `padding` pixels using the detected border colour as fill.
   - No border colour found: `ImageOps.expand` the whole image by `padding` pixels, filled with white
     (`255` for grayscale, `(255,255,255)` for RGB, `(255,255,255,255)` for RGBA; other modes such as palette images
     are converted to RGB first). Nothing is cropped.
   - Special case: if no borders were detected on any side and `padding` is `0`, the file is skipped untouched.

A consequence of the corner rule: a solid-colour image with a small differing region is treated as a bordered image
whose content is just that region, and will be cropped down to it.

## CLI options

```text
shrink_borders.py [-h] [-p PADDING] [-o OUTPUT_DIR] [-l LOG_FILE] [--dry-run] directory
```

| Option                | Default              | Effect                                                                    |
| --------------------- | -------------------- | ------------------------------------------------------------------------- |
| `directory`           | (required)           | Root directory to scan; must exist and be a directory                     |
| `-p`, `--padding`     | `5`                  | Border width in pixels applied to all four sides of every output          |
| `-o`, `--output-dir`  | none (in place)      | Write results here instead of overwriting the originals                   |
| `-l`, `--log-file`    | `shrink-borders.log` | Log file; the same messages are also printed to the console               |
| `--dry-run`           | off                  | Log what would happen (detected borders, new size) without writing files  |

## Which files are processed

`find_image_files` recurses through `directory` and picks up regular files whose extension is `.jpg`, `.jpeg` or
`.png` (case-insensitive). Everything else is ignored. Files are processed in sorted path order.

## Output layout

- **In place (default):** each image is overwritten where it is.
- **With `-o`:** the output directory is created if needed and every result is written **flat** into it as
  `OUTPUT_DIR/<original file name>`. Sub-directory structure from the input is not reproduced, so two inputs with the
  same file name in different sub-directories will overwrite each other in the output.
- **`--dry-run`:** no files or directories are created; only the log is written.

## Error handling

A file that cannot be opened or decoded (`OSError`, `ValueError`, `DecompressionBombError`) is logged as an error and
skipped; the run continues with the next file.

## Development

```bash
uv sync                           # install runtime + dev dependencies
uv run python -m pytest           # tests (tests/test_shrink_borders.py, generated images only)
uv run python -m pytest --cov     # with coverage of shrink_borders.py
uv run ruff check . && uv run ruff format .
uv run pyright
```

Docker usage is documented in [docker.md](docker.md).
