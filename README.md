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

## Project Structure
```
bluesky-notify/
├── src/                      # Main application source code
│   └── bluesky_notify/      # Main package directory
│       ├── api/             # API endpoints
│       ├── core/            # Core business logic
│       │   └── logger.py    # Centralized logging
│       ├── cli/             # CLI commands
│       ├── static/          # Static assets
│       └── templates/       # HTML templates
├── tests/                   # Test files
├── config/                  # Configuration files
├── docs/                    # Documentation
├── logs/                    # Application logs
├── requirements/            # Dependency files
│   ├── base.txt            # Base dependencies
│   └── dev.txt             # Development dependencies
├── .env                     # Environment variables
└── run.py                  # Application entry point
```

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

3. Install development dependencies:
```bash
pip install -r requirements/dev.txt
```

4. Install the package in development mode:
```bash
pip install -e ".[dev]"
```

5. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```ini
# Core Settings
DEBUG=True
SECRET_KEY=your-secret-key

# Bluesky API
BLUESKY_USERNAME=your.username.bsky.social
BLUESKY_PASSWORD=your-password

# Logging
LOG_LEVEL=INFO
LOG_FILE=bluesky_notify.log
```

6. Initialize the database:
```bash
flask db upgrade
```

## Usage

### Web Interface

1. Start the web server:
```bash
python run.py
```

2. Open your browser and navigate to `http://localhost:3001`

The web interface provides:
- Account management dashboard
- Notification preferences
- Monitoring status controls
- Account status overview

### Command Line Interface

The CLI provides quick access to core features:

```bash
# View available commands
bluesky-notify --help

# Add an account to monitor
bluesky-notify add username.bsky.social

# List monitored accounts
bluesky-notify list

# Toggle monitoring status
bluesky-notify toggle username.bsky.social

# Remove an account
bluesky-notify remove username.bsky.social

# Start the notification service
bluesky-notify start
```

## Development

### Setting Up Development Environment

1. Install development dependencies:
```bash
pip install -r requirements/dev.txt
```

2. Install pre-commit hooks:
```bash
pre-commit install
```

### Logging System

The application uses a centralized logging system with the following features:

#### Log Levels
- `DEBUG`: Detailed debugging information
- `INFO`: General operational information
- `WARNING`: Warning messages for potential issues
- `ERROR`: Error messages for serious problems
- `CRITICAL`: Critical issues that require immediate attention

#### Log Locations
- **Console**: Simple format for immediate feedback
  ```
  INFO - Starting server
  ```
- **File**: Detailed format in `logs/bluesky_notify.log`
  ```
  2023-12-06 14:30:00,123 - bluesky_notify.api - INFO - Starting server
  ```

#### Using Loggers in Code
```python
from bluesky_notify.core.logger import get_logger

# Get component-specific logger
logger = get_logger('api')  # or 'core' or 'cli'

# Log messages
logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
```

#### Log Management
- Logs are automatically rotated at 1MB
- Keeps last 5 log files
- Logs directory structure:
  ```
  logs/
  ├── bluesky_notify.log
  ├── bluesky_notify.log.1
  └── bluesky_notify.log.2
  ```

### Running Tests

```bash
pytest
```

With coverage:
```bash
pytest --cov=bluesky_notify
```

### Code Style

This project uses:
- Black for code formatting
- Flake8 for style enforcement
- isort for import sorting

Format code before committing:
```bash
black src/bluesky_notify tests
isort src/bluesky_notify tests
flake8 src/bluesky_notify tests
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
   - Review logs in `logs/bluesky_notify.log`

4. **Logging Issues**
   - Ensure `logs` directory exists and is writable
   - Check log level configuration in `.env`
   - Verify log rotation is working properly

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

Please ensure your code:
- Follows our code style (Black + Flake8)
- Includes appropriate tests
- Updates documentation as needed
- Uses proper logging practices

## License

MIT License - See LICENSE file for details
