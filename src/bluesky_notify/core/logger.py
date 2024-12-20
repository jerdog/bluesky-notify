"""
Logging configuration for the BlueSky Notification System.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
import platform
import sys
import traceback

def get_log_dir() -> str:
    """Get the log directory path."""
    system = platform.system()

    if system == 'Darwin':  # macOS
        # Use ~/Library/Logs for macOS
        log_dir = str(Path.home() / 'Library' / 'Logs')
    else:
        # Use XDG_DATA_HOME if set, otherwise ~/.local/share for other systems
        xdg_data_home = os.environ.get('XDG_DATA_HOME')
        if xdg_data_home:
            log_dir = Path(xdg_data_home)
        else:
            log_dir = Path.home() / '.local' / 'share'
        log_dir = str(log_dir / 'bluesky-notify' / 'logs')

    os.makedirs(log_dir, exist_ok=True)
    return log_dir

def get_logger(name: str, log_level: str = None) -> logging.Logger:
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

    # Test log directory is writable
    test_file = os.path.join(log_dir, '.test_write')
    try:
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
    except Exception as e:
        print(f"Error: Log directory {log_dir} is not writable: {e}")
        return logger

    # General log file handler (INFO and above)
    log_file = os.path.join(log_dir, 'bluesky-notify.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # Error log file handler (ERROR and above only)
    error_file = os.path.join(log_dir, 'bluesky-notify.error.log')
    error_handler = RotatingFileHandler(
        error_file,
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)

    # Debug console handler that respects the log level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # Add an error handler for uncaught exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.error(f"Uncaught exception:\n{error_msg}")

    sys.excepthook = handle_exception

    return logger
