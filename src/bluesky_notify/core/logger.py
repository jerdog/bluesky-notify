"""
Logging configuration for the BlueSky Notification System.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

def get_log_dir() -> str:
    """Get the log directory path."""
    # Use XDG_DATA_HOME if set, otherwise ~/.local/share
    xdg_data_home = os.environ.get('XDG_DATA_HOME')
    if xdg_data_home:
        base_dir = Path(xdg_data_home)
    else:
        base_dir = Path.home() / '.local' / 'share'
    
    log_dir = base_dir / 'bluesky-notify' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    return str(log_dir)

def get_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: The name of the logger
        log_level: Optional log level override (defaults to INFO)
    
    Returns:
        A configured logger instance
    """
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
            os.path.join(get_log_dir(), f'{name}.log'),
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
