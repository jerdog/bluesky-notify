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

### Option 2: Container Installation

Choose your preferred container runtime:

#### Docker

1. Clone the repository and configure .env as described above

2. Build and start with Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. View logs:
   ```bash
   docker-compose logs -f
   ```

4. Stop the application:
   ```bash
   docker-compose down
   ```

#### Podman

1. Clone the repository and configure .env as described above

2. Build and start with Podman Compose:
   ```bash
   # Install podman-compose if needed
   pip install podman-compose

   # Start the application
   podman-compose -f podman-compose.yml up -d
   ```

3. View logs:
   ```bash
   podman-compose logs -f
   ```

4. Stop the application:
   ```bash
   podman-compose down
   ```

#### Portainer

1. Prerequisites:
   - Running Portainer instance
   - Container registry (if using private registry)
   - Network named 'bluesky-network'
   - Volumes 'bluesky_data' and 'bluesky_logs'

2. Create the required volumes and network:
   ```bash
   # Create volumes
   docker volume create bluesky_data
   docker volume create bluesky_logs
   
   # Create network
   docker network create bluesky-network
   ```

3. In Portainer:
   - Go to Stacks → Add Stack
   - Upload the portainer-stack.yml file
   - Set environment variables:
     - REGISTRY_URL: Your registry URL (optional)
     - DOMAIN: Your domain (defaults to bluesky.localhost)
   - Deploy the stack

4. Monitor the stack through Portainer UI

## Container Management Options

### Docker Compose
- Standard Docker container management
- Suitable for local development and simple deployments
- Uses local filesystem for data persistence

### Podman
- Daemonless container engine
- Rootless containers by default
- SELinux support with :Z volume flag
- Compatible with Docker commands
- Ideal for security-focused environments

### Portainer
- Web-based container management
- Supports multiple environments
- Built-in monitoring and logging
- Easy deployment and updates
- Suitable for production environments

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
├── podman-compose.yml # Podman configuration
├── portainer-stack.yml # Portainer stack configuration
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
