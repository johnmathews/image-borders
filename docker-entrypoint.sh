#!/bin/bash
set -e

# Configuration via environment variables with defaults
PADDING="${SHRINK_BORDERS_PADDING:-5}"
OUTPUT_DIR="${SHRINK_BORDERS_OUTPUT_DIR:-}"
LOG_FILE="${SHRINK_BORDERS_LOG_FILE:-/output/shrink-borders.log}"
DRY_RUN="${SHRINK_BORDERS_DRY_RUN:-false}"
INPUT_DIR="${SHRINK_BORDERS_INPUT_DIR:-/images}"

# If user provided arguments, use them directly
if [ "$#" -gt 0 ]; then
    # Check if first arg is --help or -h
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        exec python shrink_borders.py --help
    fi

    # Pass all arguments directly to the script
    exec python shrink_borders.py "$@"
fi

# Auto-detect: if OUTPUT_DIR is empty, check if /output is mounted
if [ -z "$OUTPUT_DIR" ] && [ -d "/output" ] && [ -w "/output" ]; then
    OUTPUT_DIR="/output"
    echo "Auto-detected /output mount - saving processed images there"
fi

# Build command arguments from environment variables
CMD_ARGS=()
CMD_ARGS+=("$INPUT_DIR")
CMD_ARGS+=("--padding" "$PADDING")

# Only add output-dir if set
if [ -n "$OUTPUT_DIR" ]; then
    CMD_ARGS+=("--output-dir" "$OUTPUT_DIR")
fi

# Add log file
CMD_ARGS+=("--log-file" "$LOG_FILE")

# Add dry-run if enabled
if [ "$DRY_RUN" = "true" ]; then
    CMD_ARGS+=("--dry-run")
fi

# Execute the command with dual logging if log file is in /output
if [ -n "$LOG_FILE" ] && [[ "$LOG_FILE" == /output/* ]] && [ -d "/output" ]; then
    # Use tee for dual output (console + file)
    exec python shrink_borders.py "${CMD_ARGS[@]}" 2>&1 | tee "$LOG_FILE"
else
    # Output to console only
    exec python shrink_borders.py "${CMD_ARGS[@]}"
fi
