"""Environment-specific settings for the application."""

import os
import json
from pathlib import Path
import platform

def get_port() -> int:
    """Get the appropriate port based on the environment."""

    # For macOS, never use port 5000 as it's reserved for AirPlay
    if platform.system() == 'Darwin':
        return int(os.environ.get('PORT', 3000))  # Default to 3000 on macOS

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

    def get_settings(self) -> dict:
        """Get current settings."""
        try:
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading settings: {e}")
            return {}

    def update_settings(self, updates: dict) -> bool:
        """Update settings with new values."""
        try:
            current = self.get_settings()
            current.update(updates)

            with open(self.settings_file, 'w') as f:
                json.dump(current, f, indent=4)
            return True
        except Exception as e:
            print(f"Error updating settings: {e}")
            return False
