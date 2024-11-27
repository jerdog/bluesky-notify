# Bluesky Notify

A command-line tool for monitoring and receiving notifications from Bluesky social media accounts.

## Features

- Monitor multiple Bluesky accounts for new posts
- Desktop notifications support across platforms (macOS, Linux, Windows)
- Email notifications support (requires Mailgun configuration)
- XDG-compliant configuration storage
- SQLite database for reliable post tracking
- Cross-platform compatibility

## Installation

```bash
pip install bluesky-notify
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

### Adding an Account to Monitor

```bash
bluesky-notify add @username.bsky.social
```

Options:
- `--desktop/--no-desktop`: Enable/disable desktop notifications (default: enabled)
- `--email/--no-email`: Enable/disable email notifications (default: disabled)

### Listing Monitored Accounts

```bash
bluesky-notify list
```

### Removing an Account

```bash
bluesky-notify remove @username.bsky.social
```

### Toggling Account Status

```bash
bluesky-notify toggle @username.bsky.social
```

### Updating Notification Preferences

```bash
bluesky-notify update @username.bsky.social --desktop --no-email
```

### Starting the Notification Service

```bash
bluesky-notify start
```

The service will run continuously and check for new posts at regular intervals. Press Ctrl+C to stop the service.

### Viewing/Updating Settings

```bash
bluesky-notify settings
```

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

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please file an issue on the GitHub repository.
