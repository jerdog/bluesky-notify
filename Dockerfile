FROM python:3.11.7-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src \
    DOCKER_CONTAINER=true

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories with proper permissions
RUN mkdir -p /app/.local/share/bluesky-notify/logs /app/.local/share/bluesky-notify/data \
    && chmod -R 777 /app/.local/share/bluesky-notify

# Create a non-root user
RUN useradd -m -r appuser \
    && chown -R appuser:appuser /app

# Copy project files
COPY --chown=appuser:appuser . .

# Install the package
RUN pip install --no-cache-dir .

# Switch to non-root user
USER appuser

# Set HOME for XDG base directories
ENV HOME=/app

# Expose the application port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/ || exit 1

# Run the application
CMD ["python", "run.py"]

# Set labels
LABEL org.opencontainers.image.source="https://github.com/jerdog/bluesky-notify"
LABEL org.opencontainers.image.description="A cross-platform notification system for tracking and receiving alerts about new Bluesky social media posts."
LABEL org.opencontainers.image.licenses="MIT"
