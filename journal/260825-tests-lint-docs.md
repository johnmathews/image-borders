# 2026-08-25: Tests, lint/type tooling, docs restructure

## Why

The repo was a working single-file tool with no tests, no linting, a tracked `.pyc` and log file, and docs split
between the README and a top-level `DOCKER.md`. Bringing it in line with the global project standards (pytest +
coverage, ruff, pyright, `docs/`, `journal/`).

## What changed

### Housekeeping

- `git rm --cached` on `__pycache__/shrink_borders.cpython-313.pyc` and `shrink-borders.log`; added
  `__pycache__/`, `*.py[oc]`, `*.log`, `.venv`, `.coverage`, `htmlcov/`, `.ruff_cache/`, `.pytest_cache/` to
  `.gitignore`.
- `shrink_borders.py` is now executable (it already had a shebang).

### Tooling (`pyproject.toml`)

- `[dependency-groups] dev`: pytest, pytest-cov, ruff, pyright.
- pytest `testpaths = ["tests"]`; coverage `source = ["shrink_borders"]`.
- ruff: line length 120, target py313, rule sets E/F/I/UP/B/SIM/DTZ/BLE/PL/RUF with PLR0913/PLR0912/PLR0915/PLR2004
  ignored.
- pyright: standard mode against `.venv`.
- New `.github/workflows/test.yml` runs ruff, pyright and pytest on every push/PR. `docker-build.yml` untouched.

### Code (`shrink_borders.py`)

Ruff reported five things, all inside `process_image`: a blind `except Exception`, a `with` variable being
reassigned (`img = img.convert(...)`), two if/else blocks that should be ternaries, and an over-long help string.
Fixing these led to a small refactor that also made the logic testable without mocking:

- `white_fill_for(img)` returns the (possibly RGB-converted) image plus the white fill for its mode.
- `resolve_output_path(file_path, output_dir)` decides in-place vs. output-dir and creates the directory.
- `find_image_files(directory)` is the recursive `.jpg/.jpeg/.png` scan, pulled out of `process_directory`.
- `except Exception` became `except (OSError, ValueError, Image.DecompressionBombError)`.

One behaviour change, deliberate: previously only the "border detected" branch created the output directory, so a
no-border image processed with `-o` into a not-yet-existing directory failed (and was swallowed by the blind except as
a logged error). Both branches now go through `resolve_output_path`, which creates it. The output layout itself
(flat, `OUTPUT_DIR/<filename>`) is unchanged.

### Tests (`tests/test_shrink_borders.py`)

37 tests, 98% line coverage of `shrink_borders.py`, all images generated in memory with Pillow (no fixture files):
corner detection (match / mismatch / grayscale), content-bounds arithmetic, unequal borders becoming equal (RGB,
non-white border, grayscale), no-border images getting a white border (RGB, palette conversion, missing output dir),
in-place vs. `-o`, dry-run writing nothing, padding 0 (skip and full strip), unreadable file logged not raised,
recursive scan filtering extensions case-insensitively, flat output layout, and the CLI (`-p`, default padding,
`--dry-run`, bad directory arguments, log setup).

Two things learned while writing them:

- JPEG compression bleeds into flat borders, so a bordered JPEG does not round-trip exactly; JPEG tests use
  no-border images whose output size is deterministic.
- A solid image with a single differing pixel is, by the corner rule, a bordered image with 1x1 content. That is
  the algorithm working as designed and is now documented and tested.
- `logging.basicConfig` is a no-op under pytest (root logger already has handlers), so the log-file test clears the
  root handlers first.

### Docs

- `DOCKER.md` moved to `docs/docker.md`; README link updated.
- New `docs/how-it-works.md` describing the detection algorithm, CLI options, file discovery, output layout and
  error handling, written from the code.
- README: usage block re-checked against `--help`, corrected the claim that output always goes to a separate
  directory (default is in place), noted the flat output layout, added a Development section.
- `CLAUDE.md`: added test/lint/type-check commands and the new helper functions.
