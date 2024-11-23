"""
Entry point for the Bluesky Notification Tracker application.
"""
from bluesky_notify.core.config import load_config
from bluesky_notify.core.logger import get_logger
from bluesky_notify.api.routes import app

# Setup logging
logger = get_logger('api')

if __name__ == "__main__":
    try:
        # Load configuration from .env file
        load_config()
        logger.info("Configuration loaded successfully")
        
        # Start the application
        logger.info("Starting Bluesky Notification Tracker...")
        app.run(host="0.0.0.0", port=3001, debug=True)
    except Exception as e:
        logger.error(f"Application failed to start: {str(e)}")
        raise
