# Bluesky Notify

A cross-platform desktop notification system for Bluesky. Monitor and receive notifications from your favorite Bluesky accounts.

[![Version](https://img.shields.io/badge/version-0.5.1-blue.svg)](https://github.com/jerdog/bluesky-notify)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.1.0-blue)](https://pypi.org/project/Flask/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

https://pypi.org/project/bluesky-notify/

## Features

- Monitor multiple Bluesky accounts for new posts
- Desktop notifications support across platforms (macOS, Linux, Windows)
- Daemon mode for continuous monitoring
- Web interface for easy account management
- XDG-compliant configuration storage
- SQLite database for reliable post tracking
- Cross-platform compatibility
- Consistent CLI interface with clear version and configuration information
- Comprehensive logging system with rotation and separate error logs

## Installation

- From local / repo download
```bash
pip install bluesky-notify
```

- From PyPi
```bash

To verify the installation:
```bash
bluesky-notify --version
```

Example output:
```
Bluesky Notify v0.5.1
Config: /Users/username/.local/share/bluesky-notify

A cross-platform desktop notification system for Bluesky. Monitor and receive notifications from your favorite Bluesky accounts.

Usage: bluesky-notify [OPTIONS] COMMAND [ARGS]...

Run 'bluesky-notify start --daemon' to install and run as a system service.

Options:
  --version     Show version and exit
  --help        Show this message and exit

Commands:
  add          Add a Bluesky account to monitor.
  list         List all monitored Bluesky accounts and their notification...
  remove       Remove a Bluesky account from monitoring.
  settings     View or update application settings.
  start        Start the notification service.
  status       View the current status of the service.
  stop         Stop the notification service.
  toggle       Toggle monitoring status for a Bluesky account.
  update       Update notification preferences for a monitored account.
```

## Configuration

The application uses the XDG Base Directory Specification for storing its data:

- Configuration: `~/.config/bluesky-notify/`
- Data: `~/.local/share/bluesky-notify/`
- Cache: `~/.cache/bluesky-notify/`
- Logs:
  - macOS: `~/Library/Logs/bluesky-notify/`
  - Linux: `~/.local/share/bluesky-notify/logs/`

### Port Configuration

The web interface runs on port 3000 by default. On macOS, port 5000 is avoided as it's reserved for AirPlay. You can change the port using:

```bash
bluesky-notify settings --port NUMBER
```

## Usage

### Starting the Service

Start the service with debug logging:
```bash
bluesky-notify start --log-level DEBUG
```

Start as a system service:
```bash
bluesky-notify start --daemon
```

### Command Help

To see all available commands and options:
```bash
bluesky-notify --help
```

### Adding an Account to Monitor

```bash
bluesky-notify add username.bsky.social
```

Note: The handle should be provided without the '@' symbol.

Options:
- `--desktop/--no-desktop`: Enable/disable desktop notifications (default: enabled)

### Listing Monitored Accounts

```bash
bluesky-notify list
```

### Managing Accounts

Toggle monitoring for an account:
```bash
bluesky-notify toggle username.bsky.social
```

Remove an account:
```bash
bluesky-notify remove username.bsky.social
```

Update notification preferences:
```bash
bluesky-notify update username.bsky.social --desktop/--no-desktop
```

## Logging

The application uses a comprehensive logging system:

- Log files are stored in platform-specific locations:
  - macOS: `~/Library/Logs/bluesky-notify/`
  - Linux: `~/.local/share/bluesky-notify/logs/`

- Two log files are maintained:
  - `bluesky-notify.log`: General application logs (INFO level and above)
  - `bluesky-notify.error.log`: Error logs only (ERROR level)

- Log rotation is enabled:
  - Maximum file size: 1MB
  - Keeps up to 5 backup files
  - Rotated files are named with numerical suffixes (e.g., bluesky-notify.log.1)

- Debug logging can be enabled with:
  ```bash
  bluesky-notify start --log-level DEBUG
  ```

## Development

### Requirements

- Python 3.9 or higher
- Dependencies listed in pyproject.toml

### Setting Up Development Environment

1. Clone the repository:
```bash
git clone https://github.com/jerdog/bluesky-notify.git
cd bluesky-notify
```

2. Install development dependencies:
```bash
pip install -e ".[dev]"
```

3. Run tests:
```bash
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please file an issue on the GitHub repository.

## Version History

- 0.5.1: Remove docker functionality
- 0.5.0: Cleanup codebase, remove old functionality
- 0.4.4: Fix erratic notification issues
- 0.4.2: Enhance monitoring + logging
- 0.4.1: Validate Docker container image builds correctly, make CLI co-exist
- 0.4.0: Add web interface to daemon + terminal mode
- 0.3.0: Add daemon mode, web interface, and improved CLI help text
- 0.2.7: Fixed CLI output formatting and help text organization
- 0.2.6: Enhanced CLI interface with consistent version and config display
- 0.2.5: Improved help text formatting and command output
- 0.2.4: Added version and config information to all commands
- 0.2.3: Refined CLI presentation and version display
- 0.2.0: Initial public release

## Troubleshooting

1. **Version Check**
   - Run `bluesky-notify --version` to verify the installed version
   - Make sure you have the latest version installed

2. **No Notifications**
   - Check if desktop notifications are enabled in your system
   - Verify the notification service is running
   - Check logs in `~/.local/share/bluesky-notify/logs/`

3. **API Errors**
   - Verify Bluesky handles are entered correctly (without '@' symbol)
   - Check your internet connection
   - Ensure the Bluesky API is accessible
