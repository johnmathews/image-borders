"""Tests for shrink_borders using generated Pillow images (no fixture files)."""

import logging
import sys
from pathlib import Path

import pytest
from PIL import Image

import shrink_borders
from shrink_borders import (
    find_image_files,
    find_uniform_content_bounds,
    get_border_color,
    main,
    process_directory,
    process_image,
    resolve_output_path,
    white_fill_for,
)

WHITE = (255, 255, 255)
RED = (200, 30, 30)
BLUE = (30, 30, 200)
GREEN = (30, 200, 30)

type Borders = tuple[int, int, int, int]  # left, right, top, bottom


def bordered_image(
    content_size: tuple[int, int],
    borders: Borders,
    border_color: tuple[int, ...] | int = WHITE,
    content_color: tuple[int, ...] | int = RED,
    mode: str = "RGB",
) -> Image.Image:
    """Build an image of solid `content_color` surrounded by unequal borders of `border_color`."""
    left, right, top, bottom = borders
    cw, ch = content_size
    img = Image.new(mode, (left + cw + right, top + ch + bottom), border_color)
    content = Image.new(mode, content_size, content_color)
    img.paste(content, (left, top))
    return img


def quadrant_image(size: tuple[int, int]) -> Image.Image:
    """Build an image whose four corners are all different colours (no uniform border)."""
    w, h = size
    img = Image.new("RGB", size, RED)
    img.paste(Image.new("RGB", (w // 2, h // 2), BLUE), (w // 2, 0))
    img.paste(Image.new("RGB", (w // 2, h // 2), GREEN), (0, h // 2))
    img.paste(Image.new("RGB", (w // 2, h // 2), WHITE), (w // 2, h // 2))
    return img


def assert_uniform_border(
    img: Image.Image, padding: int, border_color: tuple[int, ...], content_color: tuple[int, ...]
) -> None:
    """Assert the image has exactly `padding` pixels of `border_color` on every side around `content_color`."""
    w, h = img.size
    for x in range(w):
        for y in range(h):
            in_border = x < padding or y < padding or x >= w - padding or y >= h - padding
            expected = border_color if in_border else content_color
            assert img.getpixel((x, y)) == expected, f"pixel {(x, y)} expected {expected}"


# --------------------------------------------------------------------------- detection


def test_get_border_color_returns_colour_when_corners_match() -> None:
    img = bordered_image((10, 10), (3, 7, 1, 4))
    assert get_border_color(img) == WHITE


def test_get_border_color_returns_none_when_corners_differ() -> None:
    assert get_border_color(quadrant_image((20, 20))) is None


def test_get_border_color_handles_grayscale() -> None:
    img = bordered_image((5, 5), (2, 2, 2, 2), border_color=255, content_color=0, mode="L")
    assert get_border_color(img) == (255,)


def test_get_border_color_borderless_solid_content_is_still_uniform() -> None:
    # Corners match but there is no border at all: colour is the content colour.
    img = Image.new("RGB", (8, 8), RED)
    assert get_border_color(img) == RED


def test_find_uniform_content_bounds_reports_each_side() -> None:
    img = bordered_image((10, 6), (3, 7, 1, 4))
    left, right, top, bottom, cl, ct, cr, cb, max_border = find_uniform_content_bounds(img, WHITE, 0)
    assert (left, right, top, bottom) == (3, 7, 1, 4)
    assert (cl, ct, cr, cb) == (3, 1, 13, 7)
    assert max_border == 7
    assert img.crop((cl, ct, cr, cb)).size == (10, 6)


def test_find_uniform_content_bounds_with_no_border() -> None:
    img = Image.new("RGB", (8, 5), RED)
    img.putpixel((4, 2), BLUE)  # any non-border pixel; corners are RED so RED is the "border"
    bounds = find_uniform_content_bounds(img, WHITE, 0)
    assert bounds == (0, 0, 0, 0, 0, 0, 8, 5, 0)


# --------------------------------------------------------------------------- helpers


@pytest.mark.parametrize(
    ("mode", "expected_fill", "expected_mode"),
    [
        ("L", 255, "L"),
        ("RGB", (255, 255, 255), "RGB"),
        ("RGBA", (255, 255, 255, 255), "RGBA"),
        ("P", (255, 255, 255), "RGB"),
    ],
)
def test_white_fill_for_each_mode(mode: str, expected_fill: int | tuple[int, ...], expected_mode: str) -> None:
    img = Image.new(mode, (4, 4))
    out, fill = white_fill_for(img)
    assert fill == expected_fill
    assert out.mode == expected_mode


def test_resolve_output_path_in_place(tmp_path: Path) -> None:
    src = tmp_path / "a.png"
    assert resolve_output_path(src, None) == src


def test_resolve_output_path_creates_output_dir(tmp_path: Path) -> None:
    src = tmp_path / "sub" / "a.png"
    out = tmp_path / "out" / "nested"
    assert resolve_output_path(src, out) == out / "a.png"
    assert out.is_dir()


# --------------------------------------------------------------------------- process_image


def test_unequal_borders_become_equal(tmp_path: Path) -> None:
    src = tmp_path / "img.png"
    bordered_image((12, 9), (15, 10, 0, 13)).save(src)

    process_image(src, padding=5, output_dir=None, dry_run=False)

    with Image.open(src) as out:
        assert out.size == (12 + 10, 9 + 10)
        assert_uniform_border(out, 5, WHITE, RED)


def test_unequal_borders_with_non_white_border_colour(tmp_path: Path) -> None:
    src = tmp_path / "img.png"
    bordered_image((6, 6), (1, 2, 3, 4), border_color=BLUE, content_color=GREEN).save(src)

    process_image(src, padding=2, output_dir=None, dry_run=False)

    with Image.open(src) as out:
        assert out.size == (10, 10)
        assert_uniform_border(out, 2, BLUE, GREEN)


def test_grayscale_borders_become_equal(tmp_path: Path) -> None:
    src = tmp_path / "img.png"
    bordered_image((4, 4), (0, 3, 2, 1), border_color=255, content_color=0, mode="L").save(src)

    process_image(src, padding=1, output_dir=None, dry_run=False)

    with Image.open(src) as out:
        assert out.mode == "L"
        assert out.size == (6, 6)
        assert out.getpixel((0, 0)) == 255
        assert out.getpixel((1, 1)) == 0
        assert out.getpixel((5, 5)) == 255


def test_no_border_image_gets_white_border(tmp_path: Path) -> None:
    src = tmp_path / "img.png"
    original = quadrant_image((20, 20))
    original.save(src)

    process_image(src, padding=4, output_dir=None, dry_run=False)

    with Image.open(src) as out:
        assert out.size == (28, 28)
        assert out.getpixel((0, 0)) == WHITE
        assert out.getpixel((27, 27)) == WHITE
        assert out.getpixel((3, 3)) == WHITE
        # Content is untouched, just shifted by the padding
        assert out.crop((4, 4, 24, 24)).tobytes() == original.tobytes()


def test_no_border_palette_image_is_converted_to_rgb(tmp_path: Path) -> None:
    src = tmp_path / "img.png"
    quadrant_image((10, 10)).convert("P").save(src)

    process_image(src, padding=1, output_dir=None, dry_run=False)

    with Image.open(src) as out:
        assert out.mode == "RGB"
        assert out.size == (12, 12)
        assert out.getpixel((0, 0)) == WHITE


def test_no_border_image_saved_to_missing_output_dir(tmp_path: Path) -> None:
    src = tmp_path / "img.png"
    quadrant_image((10, 10)).save(src)
    out_dir = tmp_path / "out"

    process_image(src, padding=2, output_dir=out_dir, dry_run=False)

    assert (out_dir / "img.png").exists()
    with Image.open(out_dir / "img.png") as out:
        assert out.size == (14, 14)


def test_output_dir_preserves_original(tmp_path: Path) -> None:
    src = tmp_path / "img.png"
    bordered_image((5, 5), (1, 4, 2, 3)).save(src)
    before = src.read_bytes()
    out_dir = tmp_path / "out"

    process_image(src, padding=1, output_dir=out_dir, dry_run=False)

    assert src.read_bytes() == before
    with Image.open(out_dir / "img.png") as out:
        assert out.size == (7, 7)


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    src = tmp_path / "img.png"
    bordered_image((5, 5), (1, 4, 2, 3)).save(src)
    before = src.read_bytes()
    out_dir = tmp_path / "out"

    process_image(src, padding=1, output_dir=out_dir, dry_run=True)
    process_image(src, padding=1, output_dir=None, dry_run=True)

    assert src.read_bytes() == before
    assert not out_dir.exists()


def test_dry_run_on_no_border_image_writes_nothing(tmp_path: Path) -> None:
    src = tmp_path / "img.png"
    quadrant_image((10, 10)).save(src)
    before = src.read_bytes()

    process_image(src, padding=3, output_dir=tmp_path / "out", dry_run=True)

    assert src.read_bytes() == before
    assert not (tmp_path / "out").exists()


def test_zero_padding_and_no_border_is_skipped(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    src = tmp_path / "img.png"
    img = Image.new("RGB", (7, 7), RED)
    # A blue cross touching every edge: corners still match (RED) but every border width is 0
    img.paste(Image.new("RGB", (1, 7), BLUE), (3, 0))
    img.paste(Image.new("RGB", (7, 1), BLUE), (0, 3))
    img.save(src)
    before = src.read_bytes()

    with caplog.at_level(logging.INFO):
        process_image(src, padding=0, output_dir=None, dry_run=False)

    assert src.read_bytes() == before
    assert "SKIP" in caplog.text


def test_zero_padding_strips_borders_entirely(tmp_path: Path) -> None:
    src = tmp_path / "img.png"
    bordered_image((4, 3), (2, 2, 2, 2)).save(src)

    process_image(src, padding=0, output_dir=None, dry_run=False)

    with Image.open(src) as out:
        assert out.size == (4, 3)
        assert_uniform_border(out, 0, WHITE, RED)


def test_solid_image_with_one_odd_pixel_is_cropped_to_that_pixel(tmp_path: Path) -> None:
    # Corners match, so the corner colour is the border and everything else is content:
    # a single differing pixel becomes a 1x1 content area with `padding` around it.
    src = tmp_path / "img.png"
    img = Image.new("RGB", (9, 9), RED)
    img.putpixel((4, 4), BLUE)
    img.save(src)

    process_image(src, padding=2, output_dir=None, dry_run=False)

    with Image.open(src) as out:
        assert out.size == (5, 5)
        assert_uniform_border(out, 2, RED, BLUE)


def test_unreadable_file_is_logged_not_raised(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    src = tmp_path / "broken.png"
    src.write_bytes(b"definitely not a png")

    with caplog.at_level(logging.ERROR):
        process_image(src, padding=1, output_dir=None, dry_run=False)

    assert "Error processing" in caplog.text
    assert src.read_bytes() == b"definitely not a png"


# --------------------------------------------------------------------------- directory scan


def _expected_size(name: str, padding: int) -> tuple[int, int]:
    side = (8 if name.lower().endswith(".png") else 12) + 2 * padding
    return (side, side)


def _populate_tree(root: Path) -> dict[str, Path]:
    files = {
        "a.png": root / "a.png",
        "b.jpg": root / "sub" / "b.jpg",
        "c.JPEG": root / "sub" / "deeper" / "c.JPEG",
        "d.PNG": root / "d.PNG",
    }
    for path in files.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() == ".png":
            # Lossless: 8x8 content inside 2px borders -> output is 8 + 2*padding
            bordered_image((8, 8), (2, 2, 2, 2)).save(path, format="PNG")
        else:
            # JPEG is lossy, so use a no-border image whose output size is deterministic: 12 + 2*padding
            quadrant_image((12, 12)).save(path, format="JPEG")
    (root / "notes.txt").write_text("skip me")
    (root / "sub" / "e.gif").write_bytes(b"GIF89a")
    (root / "sub" / "f.png.bak").write_bytes(b"")
    return files


def test_find_image_files_is_recursive_and_filters_extensions(tmp_path: Path) -> None:
    files = _populate_tree(tmp_path)
    found = find_image_files(tmp_path)
    assert found == sorted(files.values())


def test_find_image_files_empty_dir(tmp_path: Path) -> None:
    assert find_image_files(tmp_path) == []


def test_process_directory_writes_flat_output_layout(tmp_path: Path) -> None:
    src_root = tmp_path / "in"
    files = _populate_tree(src_root)
    originals = {name: path.read_bytes() for name, path in files.items()}
    out_dir = tmp_path / "out"

    process_directory(src_root, padding=1, output_dir=out_dir, dry_run=False)

    # Output is flat: one file per input, named after the input file, no sub-directories
    assert sorted(p.name for p in out_dir.iterdir()) == sorted(files)
    assert all(p.is_file() for p in out_dir.iterdir())
    for name in files:
        with Image.open(out_dir / name) as out:
            assert out.size == _expected_size(name, 1)
    # Originals are untouched
    assert {name: path.read_bytes() for name, path in files.items()} == originals


def test_process_directory_in_place(tmp_path: Path) -> None:
    files = _populate_tree(tmp_path)

    process_directory(tmp_path, padding=3, output_dir=None, dry_run=False)

    for name, path in files.items():
        with Image.open(path) as out:
            assert out.size == _expected_size(name, 3)


def test_process_directory_dry_run_makes_no_files(tmp_path: Path) -> None:
    src_root = tmp_path / "in"
    files = _populate_tree(src_root)
    originals = {name: path.read_bytes() for name, path in files.items()}
    out_dir = tmp_path / "out"

    process_directory(src_root, padding=1, output_dir=out_dir, dry_run=True)

    assert not out_dir.exists()
    assert {name: path.read_bytes() for name, path in files.items()} == originals


def test_process_directory_with_no_images_logs(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    (tmp_path / "readme.txt").write_text("nothing here")
    with caplog.at_level(logging.INFO):
        process_directory(tmp_path, padding=1, output_dir=None, dry_run=False)
    assert "No image files found" in caplog.text


# --------------------------------------------------------------------------- CLI


def run_cli(monkeypatch: pytest.MonkeyPatch, *args: str) -> None:
    monkeypatch.setattr(sys, "argv", ["shrink_borders.py", *args])
    main()


def test_cli_padding_option(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "in" / "img.png"
    src.parent.mkdir()
    bordered_image((6, 6), (3, 0, 1, 2)).save(src)
    out_dir = tmp_path / "out"

    run_cli(monkeypatch, str(src.parent), "-p", "3", "-o", str(out_dir), "-l", str(tmp_path / "log.txt"))

    with Image.open(out_dir / "img.png") as out:
        assert out.size == (12, 12)
        assert_uniform_border(out, 3, WHITE, RED)


def test_cli_default_padding_is_five(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "in" / "img.png"
    src.parent.mkdir()
    quadrant_image((6, 6)).save(src)

    run_cli(monkeypatch, str(src.parent), "-l", str(tmp_path / "log.txt"))

    with Image.open(src) as out:
        assert out.size == (16, 16)


def test_cli_dry_run_changes_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "in" / "img.png"
    src.parent.mkdir()
    bordered_image((6, 6), (3, 0, 1, 2)).save(src)
    before = src.read_bytes()
    out_dir = tmp_path / "out"

    run_cli(monkeypatch, str(src.parent), "--dry-run", "-o", str(out_dir), "-l", str(tmp_path / "log.txt"))

    assert src.read_bytes() == before
    assert not out_dir.exists()


def test_cli_missing_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    run_cli(monkeypatch, str(tmp_path / "nope"))
    assert "does not exist" in capsys.readouterr().out


def test_cli_path_is_not_a_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    f = tmp_path / "file.png"
    f.write_bytes(b"")
    run_cli(monkeypatch, str(f))
    assert "is not a directory" in capsys.readouterr().out


def test_setup_logging_writes_log_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # basicConfig is a no-op when the root logger already has handlers (pytest installs some),
    # so verify the configuration through a fresh root logger instead.
    root = logging.getLogger()
    monkeypatch.setattr(root, "handlers", [])
    log_file = tmp_path / "run.log"

    shrink_borders.setup_logging(log_file)
    try:
        logging.getLogger(shrink_borders.__name__).info("hello from test")
        for handler in root.handlers:
            handler.flush()
        assert "hello from test" in log_file.read_text()
    finally:
        for handler in root.handlers:
            handler.close()
