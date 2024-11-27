"""
Entry point for the Bluesky Notification Tracker application.
"""
import os
import sys
import asyncio
import threading
from flask import Flask

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from bluesky_notify.core.config import Config, get_data_dir
from bluesky_notify.core.logger import get_logger
from bluesky_notify.core.settings import Settings
from bluesky_notify.api.server import app, run_server
from bluesky_notify.core.notifier import BlueSkyNotifier
from bluesky_notify.core.database import db

# Setup logging
logger = get_logger('bluesky_notify')

async def run_notifier(flask_app):
    """Run the notification service."""
    try:
        notifier = BlueSkyNotifier(app=flask_app)
        logger.info("Starting notification service...")
        await notifier.run()
    except Exception as e:
        logger.error(f"Failed to start notification service: {e}")
        sys.exit(1)

def start_notifier_thread(flask_app):
    """Start the notification service in a new event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Create app context
    with flask_app.app_context():
        loop.run_until_complete(run_notifier(flask_app))
    
    loop.close()

if __name__ == "__main__":
    try:
        # Initialize configuration and settings
        config = Config()
        settings = Settings()
        current_settings = settings.get_settings()
        port = current_settings.get('port', 5001)
        
        logger.info("Starting Bluesky Notification Tracker...")
        is_container = os.environ.get('DOCKER_CONTAINER', 'false').lower() == 'true'
        
        # Start the notification service in a separate thread
        notifier_thread = threading.Thread(target=start_notifier_thread, args=(app,), daemon=True)
        notifier_thread.start()
        logger.info("Notification service started in background")
        
        # Start the web server
        run_server(
            host="0.0.0.0" if is_container else "127.0.0.1",
            port=port,
            debug=not is_container  # Disable debug mode in container
        )
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)
