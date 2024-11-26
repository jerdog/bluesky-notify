# Bluesky Notify

A cross-platform desktop notification system for Bluesky social media posts.

## Features

- Real-time desktop notifications for new Bluesky posts
- Cross-platform support (Windows, macOS, Linux)
- Configurable notification settings
- Web interface for managing tracked accounts
- Docker support for containerized deployment

## Installation

### Option 1: Using pip (Recommended for Users)

```bash
pip install bluesky-notify
```

### Option 2: Local Installation (For Development)

1. Clone the repository:
```bash
git clone https://github.com/username/bluesky-notify.git
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

4. Run the application:
```bash
python run.py
```

### Option 3: Using Docker

```bash
docker pull ghcr.io/username/bluesky-notify:latest
docker run -d --name bluesky-notify ghcr.io/username/bluesky-notify
```

Or build locally:
```bash
docker build -t bluesky-notify .
docker run -d --name bluesky-notify bluesky-notify
```

## Configuration

Before using Bluesky Notify, you need to set up your Bluesky credentials.

### Method 1: Environment Variables

```bash
export BLUESKY_HANDLE="your.handle.bsky.social"
export BLUESKY_APP_PASSWORD="your-app-password"
```

### Method 2: Configuration File

Create a config file at `~/.config/bluesky-notify/config.json`:

```json
{
  "handle": "your.handle.bsky.social",
  "app_password": "your-app-password"
}
```

### Method 3: Local Development Configuration

When running locally, copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
# Flask configuration
FLASK_APP=src/bluesky_notify
FLASK_ENV=development
SECRET_KEY=your-secret-key

# Database configuration
DATABASE_URL=sqlite:///data/bluesky_notify.db

# Notification settings
CHECK_INTERVAL=60  # seconds

# Bluesky credentials
BLUESKY_HANDLE=your.handle.bsky.social
BLUESKY_APP_PASSWORD=your-app-password
```

## Usage

### Command Line Interface

If installed via pip:
```bash
bluesky-notify start          # Start the notification service
bluesky-notify track @user    # Track a user
bluesky-notify list          # List tracked users
bluesky-notify untrack @user # Stop tracking a user
```

If running locally:
```bash
python -m bluesky_notify.cli.commands start
python -m bluesky_notify.cli.commands track @user
python -m bluesky_notify.cli.commands list
python -m bluesky_notify.cli.commands untrack @user
```

### Web Interface

1. Start the web server:
   - If installed via pip:
     ```bash
     bluesky-notify serve
     ```
   - If running locally:
     ```bash
     python run.py
     ```

2. Open http://localhost:5000 in your browser
3. Use the web interface to manage tracked accounts and notification settings

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black src/
```

### Type Checking
```bash
mypy src/
```

## Requirements

- Python 3.8 or higher
- Active Bluesky account
- App password from Bluesky settings

## Troubleshooting

1. **No notifications appearing:**
   - Check if your Bluesky credentials are correct
   - Verify that desktop notifications are enabled in your system
   - Check the logs:
     - Pip install: `~/.config/bluesky-notify/logs/app.log`
     - Local install: `./logs/app.log`

2. **Connection errors:**
   - Verify your internet connection
   - Ensure your Bluesky credentials are valid
   - Check if Bluesky's API is operational

3. **Database errors:**
   - Ensure the data directory exists
   - Check file permissions
   - For Docker: verify volume mount paths

## Support

If you encounter any issues or have questions:
1. Check the [GitHub Issues](https://github.com/username/bluesky-notify/issues)
2. Review the troubleshooting guide above
3. Open a new issue if your problem persists

## TODO

- Add GitHub Actions testing
- Streamline code where necessary/possible
- Verify notifications across platforms


## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

Please include tests and documentation updates with your changes.

## License

MIT License - see LICENSE file for details
