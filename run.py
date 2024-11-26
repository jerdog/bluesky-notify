"""
Entry point for the Bluesky Notification Tracker application.
"""
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from bluesky_notify.core.config import load_config
from bluesky_notify.core.logger import get_logger
from bluesky_notify.core.settings import get_port
from bluesky_notify.api.routes import app

# Setup logging
logger = get_logger('api')

if __name__ == "__main__":
    try:
        # Load configuration from .env file
        load_config()
        logger.info("Configuration loaded successfully")
        
        # Get the appropriate port for this environment
        port = get_port()
        logger.info(f"Starting server on port {port}")
        
        # Start the application
        logger.info("Starting Bluesky Notification Tracker...")
        is_container = os.environ.get('DOCKER_CONTAINER', 'false').lower() == 'true'
        app.run(
            host="0.0.0.0",
            port=port,
            debug=not is_container  # Disable debug mode in container
        )
    except Exception as e:
        logger.error(f"Application failed to start: {str(e)}")
