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

1. Clone the repository:
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
   SECRET_KEY=your-secret-key

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

1. Start the application:
   ```bash
   flask run
   ```

2. Access the web interface at `http://localhost:5000`

3. Add accounts to monitor:
   - Enter a Bluesky handle (e.g., @user.bsky.social)
   - Configure notification preferences
   - Click "Add Account"

4. Monitor logs for notification activity:
   ```bash
   tail -f logs/notifier.log
   ```

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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with Flask and SQLAlchemy
- Uses the Bluesky API
- Desktop notifications via desktop-notifier
- Email notifications via Mailgun
