"""Environment-specific settings for the application."""

import os
import json
from pathlib import Path
from typing import Dict, Any

def get_port() -> int:
    """Get the appropriate port based on the environment."""
    # Check if we're running in Docker
    if os.environ.get('DOCKER_CONTAINER') == 'true':
        return int(os.environ.get('PORT', 5001))  # Docker container port
    return int(os.environ.get('PORT', 3000))  # Local development port

class Settings:
    """Manages application settings."""
    
    def __init__(self):
        """Initialize Settings manager."""
        from .config import get_data_dir
        data_dir = Path(get_data_dir())
        self.settings_file = data_dir / 'settings.json'
        self._ensure_settings_file()
    
    def _ensure_settings_file(self) -> None:
        """Ensure settings file exists with default values."""
        if not self.settings_file.exists():
            # Create parent directories if they don't exist
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Default settings
            default_settings = {
                'check_interval': 60,  # seconds
                'log_level': 'INFO',
                'port': get_port()  # Use the module-level function
            }
            
            # Write default settings
            with open(self.settings_file, 'w') as f:
                json.dump(default_settings, f, indent=4)
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current settings."""
        try:
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading settings: {e}")
            return {}
    
    def update_settings(self, updates: Dict[str, Any]) -> bool:
        """Update settings with new values.
        
        Args:
            updates: Dictionary of settings to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            current = self.get_settings()
            current.update(updates)
            
            with open(self.settings_file, 'w') as f:
                json.dump(current, f, indent=4)
            return True
        except Exception as e:
            print(f"Error updating settings: {e}")
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings."""
        return self.get_settings()
