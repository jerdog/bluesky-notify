"""
Logging configuration for the BlueSky Notification System.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

def get_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: The name of the logger
        log_level: Optional log level override (defaults to INFO)
    
    Returns:
        A configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Configure logging format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Get logger
    logger = logging.getLogger(name)
    
    # Set log level
    level = getattr(logging, (log_level or 'INFO').upper())
    logger.setLevel(level)

    # Avoid duplicate handlers
    if not logger.handlers:
        # File handler
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, f'{name}.log'),
            maxBytes=1024 * 1024,  # 1MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
