# Stage 1: Builder - Install dependencies
FROM python:3.13-slim AS builder

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy dependency files first (better layer caching)
COPY pyproject.toml ./

# Install dependencies into a virtual environment
RUN uv venv && uv pip install --no-cache pillow>=11.0.0

# Stage 2: Runtime - Minimal production image
FROM python:3.13-slim

# Install runtime dependencies for Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r shrinkborders && useradd -r -g shrinkborders shrinkborders

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY shrink_borders.py ./

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/docker-entrypoint.sh

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Create directories for volumes
RUN mkdir -p /images /output && \
    chown -R shrinkborders:shrinkborders /app /images /output

# Switch to non-root user
USER shrinkborders

# Default volume mount points
VOLUME ["/images", "/output"]

# Use entrypoint script
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command shows help
CMD ["--help"]
