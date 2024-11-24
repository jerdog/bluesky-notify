"""Environment-specific settings for the application."""

import os

# Default settings
DEFAULT_PORT = 3000  # Local development port
DOCKER_PORT = 5001  # Docker container port

def get_port():
    """Get the appropriate port based on the environment."""
    # Check if we're running in Docker
    if os.environ.get('DOCKER_CONTAINER') == 'true':
        return DOCKER_PORT
    return DEFAULT_PORT
