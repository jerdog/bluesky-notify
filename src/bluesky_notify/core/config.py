"""Configuration loader for the application."""

import os
from pathlib import Path
from dotenv import load_dotenv
from .logger import get_logger

logger = get_logger('config')

def load_config() -> None:
    """Load configuration from .env file."""
    # Find the root directory (where .env is located)
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    dotenv_path = root_dir / '.env'
    
    # Load the .env file
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
        logger.info(f"Loaded configuration from {dotenv_path}")
    else:
        logger.error(f"Configuration file not found at {dotenv_path}")
        raise FileNotFoundError(f"Configuration file not found at {dotenv_path}")
    
    # Validate email configuration if email notifications are enabled
    if 'email' in os.getenv('NOTIFICATION_METHOD', '').split(','):
        required_vars = ['EMAIL_ADDRESS', 'EMAIL_PASSWORD']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            error_msg = f"Missing required email configuration variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Email configuration validated successfully")
