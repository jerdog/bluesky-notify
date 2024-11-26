FROM python:3.11.10-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src \
    DOCKER_CONTAINER=true

# Set work directory
WORKDIR /app

# Install system dependencies and build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    sqlite \
    sqlite-dev \
    && apk add --no-cache --virtual .build-deps \
    python3-dev \
    build-base

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Install the package in development mode
RUN pip install -e . \
    && apk del .build-deps

# Create necessary directories with proper permissions
RUN mkdir -p /app/src/bluesky_notify/data /app/logs /app/instance \
    && chmod -R 777 /app/src/bluesky_notify/data \
    && chmod -R 777 /app/logs \
    && chmod 777 /app/instance

# Create a non-root user and set ownership
RUN adduser -D -h /app appuser \
    && chown -R appuser:appuser /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5001/health')"

# Run the application
CMD ["python", "run.py"]
