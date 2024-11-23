# Bluesky Notification Tracker

A cross-platform notification system for tracking and receiving alerts about new Bluesky social media posts. Supports both desktop and email notifications.

## Features

- Track posts from multiple Bluesky accounts
- Flexible notification options:
  - Desktop notifications (macOS)
  - Email notifications (via Mailgun)
- Per-account notification preferences
- Prevent duplicate notifications
- Detailed logging for troubleshooting
- Docker support for easy deployment

## Prerequisites

- Python 3.11 or higher
- For desktop notifications on macOS: `terminal-notifier`
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
   ```ini
   # Mailgun Configuration
   MAILGUN_API_KEY=your_mailgun_api_key
   MAILGUN_DOMAIN=your_mailgun_domain
   MAILGUN_FROM_EMAIL=sender@example.com
   MAILGUN_TO_EMAIL=recipient@example.com

   # Optional Logging
   DEBUG=True
   LOG_LEVEL=INFO
   LOG_FILE=bluesky_notify.log
   ```

### Option 2: Docker Installation

1. Clone the repository as above

2. Copy and configure the environment file:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. Build and start the container:
   ```bash
   docker-compose up --build
   ```

## Usage

### Running Locally

```bash
python run.py
```

The application will start and begin monitoring configured Bluesky accounts.

### Running with Docker

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| MAILGUN_API_KEY | Your Mailgun API key | Yes (for email) |
| MAILGUN_DOMAIN | Your Mailgun domain | Yes (for email) |
| MAILGUN_FROM_EMAIL | Sender email address | Yes (for email) |
| MAILGUN_TO_EMAIL | Recipient email address | Yes (for email) |
| DEBUG | Enable debug mode | No |
| LOG_LEVEL | Logging level (INFO/DEBUG/ERROR) | No |
| LOG_FILE | Log file path | No |

### Notification Preferences

Notification preferences can be configured per account:
- Desktop notifications (macOS only)
- Email notifications (requires Mailgun configuration)
- Multiple notification types simultaneously

## Directory Structure

```
bluesky-notify/
├── data/               # Database and data files
│   └── backups/       # Database backups
├── logs/              # Application logs
├── src/               # Source code
├── tests/             # Test files
├── .env               # Environment configuration
├── docker-compose.yml # Docker configuration
├── Dockerfile         # Docker build file
└── requirements.txt   # Python dependencies
```

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Database Migrations

```bash
python migrate_db.py
```

## Troubleshooting

1. Check the logs in `logs/bluesky_notify.log`
2. Ensure all required environment variables are set
3. Verify Mailgun configuration for email notifications
4. For desktop notifications, ensure `terminal-notifier` is installed (macOS)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
