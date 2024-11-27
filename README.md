# Bluesky Notify

A cross-platform desktop notification system for Bluesky. Monitor and receive notifications from your favorite Bluesky accounts.

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](https://github.com/jerdog/bluesky-notify)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Features

- Monitor multiple Bluesky accounts for new posts
- Desktop notifications support across platforms (macOS, Linux, Windows)
- Daemon mode for continuous monitoring
- Email notifications support (requires Mailgun configuration)
- XDG-compliant configuration storage
- SQLite database for reliable post tracking
- Cross-platform compatibility
- Consistent CLI interface with clear version and configuration information

## Installation

```bash
pip install bluesky-notify
```

To verify the installation:
```bash
bluesky-notify --version
```

Example output:
```
Bluesky Notify v0.3.0
Config: /Users/username/.local/share/bluesky-notify

A cross-platform desktop notification system for Bluesky. Monitor and receive notifications from your favorite Bluesky accounts.

Usage: bluesky-notify [OPTIONS] COMMAND [ARGS]...

Run 'bluesky-notify start --daemon' to install and run as a system service.

Options:
  --version  Show version and exit
  --help     Show this message and exit.

Commands:
  add       Add a Bluesky account to monitor.
  list      List all monitored Bluesky accounts and their notification...
  remove    Remove a Bluesky account from monitoring.
  settings  View or update application settings.
  start     Start the notification service.
  toggle    Toggle monitoring status for a Bluesky account.
  update    Update notification preferences for a monitored account.
```

## Configuration

The application uses the XDG Base Directory Specification for storing its data:

- Configuration: `~/.config/bluesky-notify/`
- Data: `~/.local/share/bluesky-notify/`
- Cache: `~/.cache/bluesky-notify/`

### Email Notifications (Optional)

To enable email notifications, set the following environment variables:

```bash
export MAILGUN_API_KEY='your-api-key'
export MAILGUN_DOMAIN='your-domain'
export MAILGUN_FROM_EMAIL='notifications@yourdomain.com'
export MAILGUN_TO_EMAIL='your-email@example.com'
```

## Usage

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
- `--email/--no-email`: Enable/disable email notifications (default: disabled)

### Listing Monitored Accounts

```bash
bluesky-notify list
```

### Removing an Account

```bash
bluesky-notify remove username.bsky.social
```

### Toggling Account Status

```bash
bluesky-notify toggle username.bsky.social
```

### Updating Notification Preferences

```bash
bluesky-notify update username.bsky.social --desktop --no-email
```

### Starting the Notification Service

You can run the service in two ways:

1. Direct mode (run in terminal):
```bash
bluesky-notify start
```
The service will run in the foreground and can be stopped with Ctrl+C.

2. Daemon mode (install and run as system service):
```bash
bluesky-notify start --daemon
```
This will:
- Install the appropriate service file for your platform (launchd on macOS, systemd on Linux)
- Start the service automatically
- Configure it to start on system boot
- Set up logging

To stop the service:
- macOS: `launchctl unload ~/Library/LaunchAgents/com.bluesky-notify.plist`
- Linux: `systemctl --user stop bluesky-notify`

To view logs:
- macOS: Check `~/Library/Logs/bluesky-notify.log`
- Linux: Run `journalctl --user -u bluesky-notify`

### Viewing/Updating Settings

```bash
bluesky-notify settings
```

Available settings:
- Check interval (in seconds)

## Version History

- 0.3.0: Add daemon mode and improved CLI help text formatting
- 0.2.7: Fixed CLI output formatting and help text organization
- 0.2.6: Enhanced CLI interface with consistent version and config display
- 0.2.5: Improved help text formatting and command output
- 0.2.4: Added version and config information to all commands
- 0.2.3: Refined CLI presentation and version display
- 0.2.0: Initial public release

## Development

1. Clone the repository:
```bash
git clone https://github.com/jerdog/bluesky-notify.git
cd bluesky-notify
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Build the package:
```bash
python -m build
```

5. Install the built package:
```bash
pip install dist/bluesky_notify-0.3.0-py3-none-any.whl
```

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please file an issue on the GitHub repository.
