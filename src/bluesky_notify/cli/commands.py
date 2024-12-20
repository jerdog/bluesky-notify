#!/usr/bin/env python3
import click
import os
from importlib.metadata import version
from rich.console import Console
from flask import Flask
from bluesky_notify.core.notifier import BlueSkyNotifier
from bluesky_notify.core.settings import Settings
from bluesky_notify.core.database import db, add_monitored_account, list_monitored_accounts, toggle_account_status, update_notification_preferences, remove_monitored_account
from bluesky_notify.core.config import Config, get_data_dir
import asyncio
import sys
import platform
import shutil
import subprocess
import threading
from bluesky_notify.utils.network import check_service_status, is_port_in_use
import signal
import time
from bluesky_notify.core.logger import get_logger, get_log_dir
from datetime import datetime

console = Console()

# Get package version
try:
    __version__ = version("bluesky-notify")
except:
    __version__ = "unknown"

# Initialize Flask app
app = Flask(__name__)

# Load config and get data directory
config = Config()
data_dir = get_data_dir()
db_path = os.path.join(data_dir, 'bluesky_notify.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    console.print(f"[blue]Bluesky Notify v{__version__}[/blue]")
    console.print(f"Config: {config.data_dir}")
    ctx.exit()

class CustomGroup(click.Group):
    def get_help(self, ctx):
        # Print version, config, and description
        console.print(f"[blue]Bluesky Notify v{__version__}[/blue]")
        console.print(f"Config: {config.data_dir}\n")
        console.print("A cross-platform desktop notification system for Bluesky. Monitor and receive notifications from your favorite Bluesky accounts.\n")
        console.print("Usage: bluesky-notify [OPTIONS] COMMAND [ARGS]...\n")
        console.print("Run ", end="")
        console.print("'bluesky-notify start --daemon'", style="yellow", end="")
        console.print(" to install and run as a system service.\n")

        # Get the default help text and split into lines
        help_text = super().get_help(ctx)
        lines = help_text.split('\n')

        # Find the Options section and return the rest
        options_start = next(i for i, line in enumerate(lines) if line.startswith('Options:'))
        return '\n'.join(lines[options_start:])

    def invoke(self, ctx):
        # Don't print header for --version or --help
        if not ctx.protected_args and not ctx.args:
            return super().invoke(ctx)
        if ctx.protected_args[0] not in ['--version', '--help']:
            console.print(f"[blue]Bluesky Notify v{__version__}[/blue]")
            console.print(f"Config: {config.data_dir}\n")
        return super().invoke(ctx)

@click.group(cls=CustomGroup)
@click.option('--version', is_flag=True, callback=print_version, expose_value=False, is_eager=True,
              help='Show version and exit')
def cli():
    """A cross-platform desktop notification system for Bluesky. Monitor and receive notifications from your favorite Bluesky accounts."""

@cli.command()
@click.argument('handle')
@click.option('--desktop/--no-desktop', default=True, help='Enable/disable desktop notifications')
def add(handle, desktop):
    """Add a Bluesky account to monitor.

    HANDLE is the Bluesky handle without the @ symbol (e.g., username.bsky.social)"""
    with app.app_context():
        notifier = BlueSkyNotifier(app=app)

        try:
            # Get account info from Bluesky
            account_info = notifier.get_account_info(handle)

            # Add account to database
            notification_preferences = {'desktop': desktop}
            result = add_monitored_account(
                profile_data=account_info,
                notification_preferences=notification_preferences
            )

            if 'error' in result:
                console.print(f"[yellow]{result['error']}[/yellow]")
            else:
                console.print(f"[green]Successfully added {account_info['display_name'] or handle} to monitored accounts[/green]")

        except Exception as e:
            console.print(f"[red]Error adding account: {e}[/red]")

@cli.command()
def list():
    """List all monitored Bluesky accounts and their notification preferences."""
    with app.app_context():
        notifier = BlueSkyNotifier(app=app)

        accounts = list_monitored_accounts()
        if not accounts:
            console.print("[yellow]No accounts are being monitored[/yellow]")
            return

        for account in accounts:
            status = "[green]Active[/green]" if account.is_active else "[red]Inactive[/red]"
            prefs = {p.type: p.enabled for p in account.notification_preferences}
            console.print(f"{account.handle} ({account.display_name or 'No display name'}) - {status}")
            console.print(f"  Notifications: Desktop: {prefs.get('desktop', False)}")

@cli.command()
@click.argument('handle')
def toggle(handle):
    """Toggle monitoring status for a Bluesky account.

    HANDLE is the Bluesky handle without the @ symbol (e.g., username.bsky.social)"""
    with app.app_context():
        if toggle_account_status(handle):
            console.print(f"[green]Successfully toggled monitoring status for {handle}[/green]")
        else:
            console.print(f"[red]Failed to toggle status for {handle}[/red]")

@cli.command()
@click.argument('handle')
@click.option('--desktop/--no-desktop', help='Enable/disable desktop notifications')
def update(handle, desktop):
    """Update notification preferences for a monitored account.

    HANDLE is the Bluesky handle without the @ symbol (e.g., username.bsky.social)"""
    with app.app_context():
        prefs = {}
        if desktop is not None:
            prefs['desktop'] = desktop

        if update_notification_preferences(handle, prefs):
            console.print(f"[green]Successfully updated preferences for {handle}[/green]")
        else:
            console.print(f"[red]Failed to update preferences for {handle}[/red]")

@cli.command()
@click.argument('handle')
def remove(handle):
    """Remove a Bluesky account from monitoring.

    HANDLE is the Bluesky handle without the @ symbol (e.g., username.bsky.social)"""
    with app.app_context():
        if remove_monitored_account(handle):
            console.print(f"[green]Successfully removed {handle} from monitored accounts[/green]")
        else:
            console.print(f"[red]Failed to remove {handle}[/red]")

@cli.command()
def status():
    """Show the current status of the notification service."""
    settings = Settings()
    config = Config()

    # Get service status
    service_status = check_service_status()
    port = settings.get_settings().get('port', 3000)
    web_running = is_port_in_use(port)

    # Print status with rich formatting
    console.print("\n[bold]Bluesky Notify Status[/bold]")
    console.print("─" * 50)

    # Service Status
    if service_status['running']:
        mode = service_status['mode'].title()
        console.print(f"[green]● Service Running[/green] (Mode: {mode})")
        if service_status['pid']:
            console.print(f"   Process ID: {service_status['pid']}")
    else:
        console.print("[red]○ Service Not Running[/red]")

    # Web Interface
    if web_running:
        console.print(f"[green]● Web Interface Running[/green]")
        console.print(f"   URL: [link=http://127.0.0.1:{port}]http://127.0.0.1:{port}[/link]")
    else:
        console.print("[red]○ Web Interface Not Running[/red]")

    # Data Directory
    data_dir = config.get_data_dir()
    console.print("\n[bold]Data Directory:[/bold]")
    console.print(f"[blue]{data_dir}[/blue]")

    # Configuration
    console.print("\n[bold]Configuration:[/bold]")
    current = settings.get_settings()
    console.print(f"Check Interval: {current.get('check_interval', 60)} seconds")
    console.print(f"Log Level: {current.get('log_level', 'INFO')}")
    console.print(f"Web Port: {current.get('port', 3000)}")

@cli.command()
@click.option('--interval', type=int, help='Check interval in seconds (default: 60)')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR'], case_sensitive=False),
              help='Logging level (default: INFO)')
@click.option('--port', type=int, help='Web interface port (default: 3000)')
def settings(interval, log_level, port):
    """View or update application settings.

    Available options:
      --interval    Check interval in seconds (default: 60)
      --log-level   Logging level: DEBUG, INFO, WARNING, or ERROR (default: INFO)
      --port        Web interface port (default: 3000)

    Example:
      bluesky-notify settings --interval 30 --log-level DEBUG --port 3001
    """
    settings = Settings()
    logger = get_logger('bluesky_notify')

    # Get current settings before update
    old_settings = settings.get_settings()
    old_port = old_settings.get('port', 3000)

    # Update settings if provided
    updates = {}
    if interval is not None:
        updates['check_interval'] = interval
    if log_level is not None:
        updates['log_level'] = log_level.upper()
    if port is not None:
        updates['port'] = port

    if updates:
        if settings.update_settings(updates):
            console.print("[green]Settings updated successfully![/green]")

            # If port was changed, check if we need to restart the web server
            if 'port' in updates and updates['port'] != old_port:
                logger.info(f"Port changed from {old_port} to {updates['port']}, restarting web server...")

                # Check if old port is in use (indicating our server is running)
                if is_port_in_use(old_port):
                    # Stop the current server
                    from bluesky_notify.api.server import shutdown_server
                    shutdown_server()
                    time.sleep(1)  # Give it a moment to shut down

                    # Verify old port is free
                    if is_port_in_use(old_port):
                        logger.warning(f"Port {old_port} is still in use after shutdown attempt")

                    # Start the server with new port
                    from bluesky_notify.api.server import run_server
                    def run_web_server():
                        try:
                            run_server(host='127.0.0.1', port=updates['port'])
                        except Exception as e:
                            logger.error(f"Error starting web server on port {updates['port']}: {e}")
                            # Signal the main thread
                            os.kill(os.getpid(), signal.SIGINT)

                    web_thread = threading.Thread(target=run_web_server, daemon=True)
                    web_thread.start()

                    # Give the server a moment to start
                    time.sleep(1)

                    # Verify new port is in use
                    if is_port_in_use(updates['port']):
                        logger.info(f"Web server restarted successfully on port {updates['port']}")
                    else:
                        logger.error(f"Failed to start web server on port {updates['port']}")

                else:
                    logger.info(f"No web server running on port {old_port}")
        else:
            console.print("[red]Failed to update settings[/red]")

    # Display current settings
    current = settings.get_settings()
    console.print("\n[bold]Current Settings:[/bold]")
    console.print(f"Check Interval: {current.get('check_interval', 60)} seconds")
    console.print(f"Log Level: {current.get('log_level', 'INFO')}")
    console.print(f"Web Interface Port: {current.get('port', 3000)}")

    # Show available options
    console.print("\n[bold]Available Options:[/bold]")
    console.print("--interval NUMBER    Set check interval (in seconds, minimum: 30)")
    console.print("--log-level LEVEL    Set log level (DEBUG, INFO, WARNING, or ERROR)")
    console.print("--port NUMBER        Set web interface port (1024-65535)")

def get_executable_path():
    """Find the bluesky-notify executable in common installation paths."""
    possible_paths = [
        '/opt/local/bin/bluesky-notify',  # MacPorts
        '/usr/local/bin/bluesky-notify',  # System Python
        '/opt/homebrew/bin/bluesky-notify',  # Homebrew
        os.path.expanduser('~/.local/bin/bluesky-notify'),  # User install
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    # If not found in common paths, try to find it in PATH
    try:
        which_result = subprocess.run(['which', 'bluesky-notify'],
                                    capture_output=True,
                                    text=True,
                                    check=True)
        return which_result.stdout.strip()
    except subprocess.CalledProcessError:
        pass

    raise click.ClickException("Could not find bluesky-notify executable. Please ensure it's installed correctly.")

@cli.command()
@click.option('-d', '--daemon', is_flag=True, help='Install and run as a system service')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR'], case_sensitive=False),
              default='INFO', help='Set the logging level')
def start(daemon, log_level):
    """Start the notification service.

    Run with --daemon to install and run as a system service (supported on macOS and Linux).
    The web interface is always available at the configured port (default: 3000)."""

    settings = Settings()
    port = settings.get_settings().get('port', 3000)

    # Configure logging first
    logger = get_logger(__name__, log_level)

    # Set up exception hook to log uncaught exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

    if daemon:
        system = platform.system()
        if system == 'Darwin':  # macOS
            # Get package directory
            package_dir = os.path.dirname(os.path.dirname(__file__))
            plist_src = os.path.join(package_dir, 'services/launchd/com.bluesky-notify.plist')

            # Create LaunchAgents directory if it doesn't exist
            launch_agents_dir = os.path.expanduser('~/Library/LaunchAgents')
            os.makedirs(launch_agents_dir, exist_ok=True)

            # Create necessary directories
            log_dir = os.path.expanduser('~/Library/Logs')
            os.makedirs(log_dir, exist_ok=True)

            # Ensure log files exist and are writable
            for log_file in ['bluesky-notify.log', 'bluesky-notify.error.log']:
                log_path = os.path.join(log_dir, log_file)
                try:
                    with open(log_path, 'a') as f:
                        f.write(f"Log file initialized at {datetime.now()}\n")
                    os.chmod(log_path, 0o644)
                except Exception as e:
                    console.print(f"[red]Error creating log file {log_path}: {e}[/red]")
                    return

            # Copy plist file
            plist_dest = os.path.join(launch_agents_dir, 'com.bluesky-notify.plist')
            shutil.copy2(plist_src, plist_dest)

            # Replace placeholders in plist file
            with open(plist_dest, 'r') as f:
                content = f.read()

            # Replace paths with absolute paths
            home_dir = os.path.expanduser('~')
            content = content.replace('/Users/jerdog', home_dir)
            content = content.replace('/opt/local/bin/bluesky-notify', get_executable_path())
            content = content.replace('~/Library/Logs', f'{home_dir}/Library/Logs')

            with open(plist_dest, 'w') as f:
                f.write(content)

            # Set correct permissions
            os.chmod(plist_dest, 0o644)

            # Load the service
            try:
                subprocess.run(['launchctl', 'unload', plist_dest], capture_output=True)
                subprocess.run(['launchctl', 'load', '-w', plist_dest], check=True)
                console.print("[green]Service installed and started successfully![/green]")
                console.print(f"Logs will be available at:\n- ~/Library/Logs/bluesky-notify.log\n- ~/Library/Logs/bluesky-notify.error.log")
                console.print(f"\nWeb interface will be available at: [link=http://127.0.0.1:{port}]http://127.0.0.1:{port}[/link]")
                console.print("\nNote: It may take a few seconds for the web interface to start.")
                return
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Error starting service: {e}[/red]")
                sys.exit(1)

        elif system == 'Linux':
            # Get package directory
            package_dir = os.path.dirname(os.path.dirname(__file__))
            service_src = os.path.join(package_dir, 'services/systemd/bluesky-notify.service')

            # Create systemd user directory if it doesn't exist
            systemd_dir = os.path.expanduser('~/.config/systemd/user')
            os.makedirs(systemd_dir, exist_ok=True)

            # Copy service file
            service_dest = os.path.join(systemd_dir, 'bluesky-notify.service')
            shutil.copy2(service_src, service_dest)

            # Replace %i with actual username in service file
            with open(service_dest, 'r') as f:
                content = f.read()
            content = content.replace('%i', os.getenv('USER'))
            content = content.replace('/opt/homebrew/bin/bluesky-notify', get_executable_path())
            with open(service_dest, 'w') as f:
                f.write(content)

            # Enable and start the service
            try:
                subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
                subprocess.run(['systemctl', '--user', 'enable', 'bluesky-notify'], check=True)
                subprocess.run(['systemctl', '--user', 'start', 'bluesky-notify'], check=True)
                console.print("[green]Service installed and started successfully![/green]")
                console.print(f"Web interface will be available at: [link=http://127.0.0.1:{port}]http://127.0.0.1:{port}[/link]")
                console.print("\nNote: It may take a few seconds for the web interface to start.")
                console.print("To view logs, run: journalctl --user -u bluesky-notify")
                return
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Error starting service: {e}[/red]")
                sys.exit(1)
        else:
            console.print(f"[red]Daemon mode is not supported on {system}[/red]")
            sys.exit(1)

    # If not running as daemon, proceed with normal start
    with app.app_context():
        # Initialize our logger with specified level
        logger = get_logger('bluesky_notify', log_level=log_level)

        logger.info(f"Starting Bluesky Notify v{__version__}")
        logger.info(f"Config directory: {config.data_dir}")
        log_dir = get_log_dir()
        logger.info(f"Log directory: {log_dir}")
        logger.debug(f"Log level: {log_level}")

        # Verify log directory exists and is writable
        try:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            test_file = os.path.join(log_dir, 'test.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            logger.info("Log directory is writable")
        except Exception as e:
            logger.error(f"Error accessing log directory: {e}")
            return

        notifier = BlueSkyNotifier(app=app)

        # Start web interface in a separate thread
        from bluesky_notify.api.server import run_server
        import webbrowser

        def run_web_server():
            try:
                # Get current port from settings, ensure we use 3000 as default for local development
                current_settings = settings.get_settings()
                server_port = current_settings.get('port', 3000)

                # If port is 5000 on macOS, switch to 3000
                if server_port == 5000 and platform.system() == 'Darwin':
                    logger.warning("Port 5000 is reserved on macOS, switching to port 3000")
                    server_port = 3000
                    # Update settings
                    settings.update_settings({'port': server_port})

                logger.debug(f"Attempting to start web server on port {server_port}")

                # More thorough port check
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('127.0.0.1', server_port))
                if result == 0:
                    logger.error(f"Port {server_port} is already in use")
                    sock.close()
                    os.kill(os.getpid(), signal.SIGINT)
                    return
                sock.close()
                logger.debug(f"Port {server_port} is available")

                # Open web browser after a short delay
                def open_browser():
                    time.sleep(1.5)  # Wait for server to start
                    url = f'http://127.0.0.1:{server_port}'
                    logger.info(f"Opening web interface at {url}")
                    webbrowser.open(url)

                browser_thread = threading.Thread(target=open_browser, name="BrowserOpener")
                browser_thread.daemon = True
                browser_thread.start()

                logger.info(f"Starting web interface on port {server_port}")
                # Start Flask with debug output
                run_server(host='127.0.0.1', port=server_port, debug=True)
            except Exception as e:
                logger.error(f"Error in web server: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Signal the main thread to shut down
                os.kill(os.getpid(), signal.SIGINT)

        def run_notifier_service():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                with app.app_context():
                    notifier = BlueSkyNotifier(app=app)
                    logger.info("Starting notification service")
                    loop.run_until_complete(notifier.run())
            except Exception as e:
                logger.error(f"Error in notification service: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Signal the main thread to shut down
                os.kill(os.getpid(), signal.SIGINT)

        # Start both services in separate threads
        web_thread = threading.Thread(target=run_web_server, name="WebServer")
        notifier_thread = threading.Thread(target=run_notifier_service, name="NotifierService")

        # Make threads daemon so they exit when main thread exits
        web_thread.daemon = True
        notifier_thread.daemon = True

        # Start threads
        web_thread.start()
        notifier_thread.start()

        logger.info("Services started. Press Ctrl+C to stop.")

        try:
            # Keep main thread alive and handle Ctrl+C
            while True:
                time.sleep(1)

                # Check if threads are still alive
                if not web_thread.is_alive():
                    logger.error("Web server thread died unexpectedly")
                    break
                if not notifier_thread.is_alive():
                    logger.error("Notifier thread died unexpectedly")
                    break

        except KeyboardInterrupt:
            logger.warning("Stopping services...")
            notifier.stop()
            # Shutdown the web server
            from bluesky_notify.api.server import shutdown_server
            shutdown_server()
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error in main thread: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            from bluesky_notify.api.server import shutdown_server
            shutdown_server()
            sys.exit(1)

@cli.command()
def stop():
    """Stop the notification service."""
    system = platform.system()
    service_status = check_service_status()

    if not service_status['running']:
        console.print("[yellow]Service is not running[/yellow]")
        return

    try:
        if service_status['mode'] == 'daemon':
            if system == 'Darwin':  # macOS
                plist_path = os.path.expanduser('~/Library/LaunchAgents/com.bluesky-notify.plist')
                subprocess.run(
                    ['launchctl', 'unload', plist_path],
                    capture_output=True
                )
                # Also kill any remaining processes
                for pid in service_status['pids']:
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except:
                        pass
                console.print("[green]Daemon service stopped successfully[/green]")
            elif system == 'Linux':
                subprocess.run(
                    ['systemctl', '--user', 'stop', 'bluesky-notify'],
                    check=True
                )
                # Also kill any remaining processes
                for pid in service_status['pids']:
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except:
                        pass
                console.print("[green]Daemon service stopped successfully[/green]")
            else:
                console.print("[red]Daemon mode not supported on this platform[/red]")
        else:  # Terminal mode
            killed = False
            for pid in service_status['pids']:
                try:
                    os.kill(pid, signal.SIGTERM)
                    killed = True
                except:
                    pass
            if killed:
                console.print("[green]Terminal service stopped successfully[/green]")
            else:
                console.print("[red]Could not find process to stop[/red]")

        # Try to stop web interface by sending request
        try:
            import requests
            settings = Settings()
            port = settings.get_settings().get('port', 3000)
            requests.get(f'http://127.0.0.1:{port}/shutdown', timeout=1)
        except:
            pass  # Web interface might already be down

        # Verify service is stopped
        time.sleep(1)  # Give processes time to stop
        new_status = check_service_status()
        if new_status['running']:
            console.print("[yellow]Warning: Service may still be running[/yellow]")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error stopping service: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

# Export the CLI function as main for the entry point
def main():
    cli()

if __name__ == '__main__':
    main()
