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
RUN mkdir -p /app/src/bluesky_notify/data /app/logs /app/instance \
    && chmod -R 777 /app/src/bluesky_notify/data \
    && chmod -R 777 /app/logs \
    && chmod 777 /app/instance

# Create a non-root user
RUN useradd -m -r appuser \
    && chown -R appuser:appuser /app

# Copy project files
COPY --chown=appuser:appuser . .

# Install the package
RUN pip install --no-cache-dir .

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5001/health')"

# Run the application
CMD ["python", "run.py"]
