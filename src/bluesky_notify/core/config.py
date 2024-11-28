"""Configuration loader for the application."""

import os
from pathlib import Path
from typing import Dict, Any
from .logger import get_logger

logger = get_logger('config')

def get_data_dir() -> str:
    """Get the data directory path."""
    # First check if XDG_DATA_HOME is set
    xdg_data_home = os.environ.get('XDG_DATA_HOME')
    if xdg_data_home:
        base_dir = Path(xdg_data_home)
    else:
        # Default to ~/.local/share
        base_dir = Path.home() / '.local' / 'share'
    
    data_dir = base_dir / 'bluesky-notify'
    # Ensure the directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir)

class Config:
    """Configuration manager for the application."""
    
    def __init__(self):
        """Initialize Config manager with default values."""
        self.data_dir = get_data_dir()
        self._config = {
            'NOTIFICATION_METHOD': 'desktop',
            'CHECK_INTERVAL': '60',
            'LOG_LEVEL': 'INFO',
            'DATABASE_URL': f'sqlite:///{self.data_dir}/bluesky_notify.db'
        }
    
    def get_data_dir(self) -> str:
        """Get the data directory path."""
        return self.data_dir
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
    
    def get_all(self) -> Dict[str, str]:
        """Get all configuration values.
        
        Returns:
            Dict of all configuration values
        """
        return self._config.copy()
