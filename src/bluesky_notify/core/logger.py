"""
Logging configuration for the BlueSky Notification System.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
import platform

def get_log_dir() -> str:
    """Get the log directory path."""
    system = platform.system()
    
    if system == 'Darwin':  # macOS
        # Use ~/Library/Logs for macOS
        log_dir = Path.home() / 'Library' / 'Logs'
    else:
        # Use XDG_DATA_HOME if set, otherwise ~/.local/share for other systems
        xdg_data_home = os.environ.get('XDG_DATA_HOME')
        if xdg_data_home:
            log_dir = Path(xdg_data_home)
        else:
            log_dir = Path.home() / '.local' / 'share'
        log_dir = log_dir / 'bluesky-notify' / 'logs'
    
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
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Get logger
    logger = logging.getLogger(name)
    
    # Set log level
    level = getattr(logging, (log_level or 'INFO').upper())
    logger.setLevel(level)

    # Remove any existing handlers
    logger.handlers = []

    # Get log directory
    log_dir = get_log_dir()
    
    # General log file handler (INFO and above, but not ERROR)
    class InfoFilter(logging.Filter):
        def filter(self, record):
            return record.levelno < logging.ERROR

    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Test log directory is writable
    test_file = os.path.join(log_dir, '.test_write')
    try:
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
    except Exception as e:
        print(f"Error: Log directory {log_dir} is not writable: {e}")
        return logger

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'bluesky-notify.log'),
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    file_handler.addFilter(InfoFilter())
    logger.addHandler(file_handler)

    # Error log file handler (ERROR and above only)
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'bluesky-notify.error.log'),
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)

    # Debug console handler that respects the log level
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)  # Use the same level as the logger
    logger.addHandler(console_handler)
    
    # Test logging
    logger.debug(f"Logger initialized with level {level}")
    logger.debug(f"Log directory: {log_dir}")
    logger.debug("Testing debug message")
    logger.info("Testing info message")
    
    return logger
