# Bluesky Notification Tracker

A cross-platform notification system for tracking and receiving alerts about new Bluesky social media posts. Supports both desktop and email notifications.

## Features

- Track posts from multiple Bluesky accounts
- Flexible notification options:
  - Desktop notifications (macOS, Linux, Windows)
  - Email notifications (via Mailgun)
- Per-account notification preferences
- Prevent duplicate notifications
- Detailed logging for troubleshooting
- Docker support for easy deployment
- SQLite database for persistent storage
- Automatic retries with exponential backoff
- Web interface for account management

## Prerequisites

- Python 3.11 or higher
- For desktop notifications:
  - macOS: `terminal-notifier`
  - Linux: `notify-send`
  - Windows: Windows 10 or higher
- Mailgun account (for email notifications)
- Docker (optional, for containerized deployment)

## Installation

### Option 1: Local Installation

1. [Fork](https://github.com/jerdog/bluesky-notify/fork) and then Clone the repository:
   ```bash
   git clone <repository-url>
   cd bluesky-notify
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Unix/macOS
   # OR
   venv\Scripts\activate     # On Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` with your configuration:
   ```env
   # Flask configuration
   FLASK_APP=src/bluesky_notify
   FLASK_ENV=development
   SECRET_KEY=your-secret-key ## ex: `npx node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"`

   # Database configuration
   DATABASE_URL=sqlite:///data/bluesky_notify.db

   # Notification settings
   CHECK_INTERVAL=60  # seconds

   # Email configuration (optional)
   MAILGUN_API_KEY=your-mailgun-api-key
   MAILGUN_DOMAIN=your-mailgun-domain
   MAILGUN_FROM_EMAIL=notifications@yourdomain.com
   MAILGUN_TO_EMAIL=your@email.com
   ```

### Option 2: Docker Installation

1. Build and run using Docker Compose:
   ```bash
   docker-compose up -d
   ```

2. Or using Podman:
   ```bash
   podman-compose up -d
   ```

## Usage

### Web Interface

1. Start the application:
   ```bash
   flask run
   ```

2. Access the web interface at `http://localhost:5000`

3. Add accounts to monitor:
   - Enter a Bluesky handle (e.g., @user.bsky.social)
   - Configure notification preferences
   - Click "Add Account"

### CLI Commands

The application provides a command-line interface for managing monitored accounts:

```bash
# Add an account to monitor
python -m bluesky_notify.cli.commands add @handle.bsky.social [--desktop/--no-desktop] [--email/--no-email]

# List monitored accounts
python -m bluesky_notify.cli.commands list

# Toggle monitoring status
python -m bluesky_notify.cli.commands toggle @handle.bsky.social

# Update notification preferences
python -m bluesky_notify.cli.commands update @handle.bsky.social [--desktop/--no-desktop] [--email/--no-email]

# Remove an account
python -m bluesky_notify.cli.commands remove @handle.bsky.social

# Update settings
python -m bluesky_notify.cli.commands settings [--interval SECONDS] [--log-level LEVEL]

# Start the notification service
python -m bluesky_notify.cli.commands start
```

### Docker Usage

1. Build and start the container:
   ```bash
   docker-compose up -d --build
   ```

2. View logs:
   ```bash
   docker-compose logs -f
   ```

3. Stop the container:
   ```bash
   docker-compose down
   ```

The Docker container uses a volume mount to persist data in `./src/bluesky_notify/data/bluesky_notify.db`. This ensures your monitored accounts and preferences are preserved between container restarts.

## Data Storage

The application stores its data in the following locations:

- Local installation: `./src/bluesky_notify/data/bluesky_notify.db`
- Docker installation: Volume mounted at `./src/bluesky_notify/data/bluesky_notify.db`

## Troubleshooting

### Common Issues

1. **Database Errors**
   - Ensure the data directory exists: `./src/bluesky_notify/data`
   - Check file permissions
   - For Docker: verify volume mount paths

2. **Notification Issues**
   - Desktop notifications: Check system notification settings
   - Email notifications: Verify Mailgun credentials
   - Docker desktop notifications: Only supported on Linux host with proper setup

3. **Authentication Errors**
   - Verify Bluesky credentials in `.env`
   - Check network connectivity
   - Ensure rate limits haven't been exceeded

### Logs

- Application logs: `./logs/bluesky_notify.log`
- Docker logs: `docker-compose logs -f`

## API Endpoints

- `GET /api/accounts` - List monitored accounts
- `POST /api/accounts` - Add new account to monitor
- `DELETE /api/accounts/<handle>` - Remove monitored account
- `PUT /api/accounts/<handle>/preferences` - Update notification preferences

## Architecture

The application is structured into several core components:

- `core/notifier.py` - Main notification service
- `core/database.py` - Database models and operations
- `core/config.py` - Configuration management
- `api/routes.py` - API endpoints
- `templates/` - Web interface templates
- `static/` - Static assets

## Development

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Format code:
   ```bash
   black src/
   ```

4. Check type hints:
   ```bash
   mypy src/
   ```

## TODO

- Add GitHub Actions testing
- Streamline code where necessary/possible
- Verify notifications across platforms
- 

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

Please include tests and documentation updates with your changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Flask and SQLAlchemy
- Uses the Bluesky API
- Desktop notifications via desktop-notifier
- Email notifications via Mailgun
