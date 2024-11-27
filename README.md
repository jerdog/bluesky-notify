# Bluesky Notify

A cross-platform desktop notification system for Bluesky. Monitor and receive notifications from your favorite Bluesky accounts.

[![Version](https://img.shields.io/badge/version-0.2.7-blue.svg)](https://github.com/jerdog/bluesky-notify)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Features

- Monitor multiple Bluesky accounts for new posts
- Desktop notifications support across platforms (macOS, Linux, Windows)
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
Bluesky Notify v0.2.7
Config: /Users/username/.local/share/bluesky-notify
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

```bash
bluesky-notify start
```

The service will run continuously and check for new posts at regular intervals (default: 60 seconds). Press Ctrl+C to stop the service.

### Viewing/Updating Settings

```bash
bluesky-notify settings
```

Available settings:
- Check interval (in seconds)

## Version History

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
pip install dist/bluesky_notify-0.2.7-py3-none-any.whl
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
