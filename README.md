# Bluesky Notification Tracker

A cross-platform desktop application to monitor and track notifications from multiple Bluesky accounts with seamless integration and user-friendly features.

## Features
- **Multi-Account Support**: Monitor multiple Bluesky accounts simultaneously
- **Desktop Notifications**: Rich preview notifications for new posts
- **Account Management**:
  - Add/remove monitored accounts
  - Enable/disable monitoring per account
  - Configure notification preferences
  - View account status and details
- **Dual Interfaces**:
  - Modern web interface with Bootstrap 5.3.2
  - Command-line interface for automation
- **Secure Authentication**: Safe credential storage and handling
- **Cross-Platform**: Works on macOS, Linux, and Windows

## Prerequisites
- Python 3.8+
- Bluesky account credentials
- Internet connection
- Modern web browser (for web interface)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd bluesky-notify
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```

5. Edit `.env` with your Bluesky credentials:
```ini
BLUESKY_USERNAME=your.username.bsky.social
BLUESKY_PASSWORD=your-password
```

6. Initialize the database:
```bash
export FLASK_APP=app.py
flask db upgrade
```

## Usage

### Web Interface

1. Start the web server:
```bash
python app.py
```

2. Open your browser and navigate to `http://localhost:3001`

3. Use the web interface to:
- View all monitored accounts
- Add new accounts to monitor
- Enable/disable account monitoring
- Remove accounts from monitoring

### Command Line Interface

The CLI provides quick access to all features:

```bash
# View available commands
./cli.py --help

# Add an account to monitor
./cli.py add username.bsky.social

# List monitored accounts
./cli.py list

# Toggle monitoring status
./cli.py toggle username.bsky.social

# Remove an account
./cli.py remove username.bsky.social

# Start the notification service
./cli.py start
```

## Architecture

### Components
- **Frontend**: Bootstrap 5.3.2, Vanilla JavaScript
- **Backend**: Flask with SQLAlchemy ORM
- **Database**: SQLite with Flask-Migrate for schema management
- **Notifications**: desktop-notifier
- **API Client**: atproto

### Project Structure
```
bluesky-notify/
├── app.py              # Web server and API endpoints
├── cli.py              # Command-line interface
├── database.py         # Database models and management
├── notifier.py         # Core notification logic
├── migrations/         # Database migrations
├── requirements.txt    # Python dependencies
├── static/            
│   ├── app.js         # Frontend JavaScript
│   └── styles.css     # Custom styles
└── templates/
    └── index.html     # Main web interface
```

## Development

### Setting Up Development Environment

1. Install development dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize database migrations:
```bash
export FLASK_APP=app.py
flask db migrate -m "initial migration"
flask db upgrade
```

### Database Migrations

To create a new migration:
```bash
flask db migrate -m "description of changes"
flask db upgrade
```

To rollback a migration:
```bash
flask db downgrade
```

## Troubleshooting

1. **Database Issues**
   - Ensure migrations are up to date: `flask db upgrade`
   - Check SQLite file permissions
   - Verify database path in configuration

2. **Authentication Issues**
   - Confirm Bluesky credentials in `.env`
   - Check internet connectivity
   - Verify Bluesky API status

3. **Notification Issues**
   - Check system notification permissions
   - Verify account monitoring is enabled
   - Review logs in `bluesky_notify.log`

## Security

- Environment variables for sensitive data
- No credential storage in code or logs
- Secure API authentication
- Input validation and sanitization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

Please ensure your code:
- Follows the existing style
- Includes appropriate tests
- Updates documentation as needed

## License

MIT License - See LICENSE file for details
