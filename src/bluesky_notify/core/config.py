"""Configuration loader for the application."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from .logger import get_logger

logger = get_logger('config')

def get_data_dir() -> str:
    """Get the data directory path."""
    # Use the package's data directory
    package_dir = Path(__file__).resolve().parent.parent
    data_dir = str(package_dir / 'data')
    
    # Ensure the directory exists
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"Using data directory: {data_dir}")
    return data_dir

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
        logger.warning(f"Configuration file not found at {dotenv_path}, using default values")

class Config:
    """Configuration manager for the application."""
    
    def __init__(self):
        """Initialize Config manager."""
        load_config()
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return os.getenv(key, default)
    
    def validate_email_config(self) -> bool:
        """Validate email configuration.
        
        Returns:
            bool: True if valid, False otherwise
        """
        if 'email' in self.get('NOTIFICATION_METHOD', '').split(','):
            required_vars = [
                'MAILGUN_API_KEY',
                'MAILGUN_DOMAIN',
                'MAILGUN_FROM_EMAIL',
                'MAILGUN_TO_EMAIL'
            ]
            missing_vars = [var for var in required_vars if not self.get(var)]
            
            if missing_vars:
                logger.error(f"Missing required email configuration variables: {', '.join(missing_vars)}")
                return False
            
            logger.info("Email configuration validated successfully")
            return True
        return True  # Email notifications not enabled, so config is valid
    
    def get_all(self) -> Dict[str, str]:
        """Get all configuration values.
        
        Returns:
            Dict of all configuration values
        """
        data_dir = get_data_dir()
        db_path = os.path.join(data_dir, 'bluesky_notify.db')
        
        return {
            'NOTIFICATION_METHOD': self.get('NOTIFICATION_METHOD', 'desktop'),
            'CHECK_INTERVAL': self.get('CHECK_INTERVAL', '60'),
            'LOG_LEVEL': self.get('LOG_LEVEL', 'INFO'),
            'MAILGUN_DOMAIN': self.get('MAILGUN_DOMAIN', ''),
            'MAILGUN_FROM_EMAIL': self.get('MAILGUN_FROM_EMAIL', ''),
            'MAILGUN_TO_EMAIL': self.get('MAILGUN_TO_EMAIL', ''),
            'DATABASE_URL': self.get('DATABASE_URL', f'sqlite:///{db_path}')
        }
