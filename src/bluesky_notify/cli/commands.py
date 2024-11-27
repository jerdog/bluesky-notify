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
from pathlib import Path

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
app.config.from_object(config)
db_path = os.path.join(config.data_dir, 'bluesky_notify.db')
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
@click.option('--email/--no-email', default=False, help='Enable/disable email notifications')
def add(handle, desktop, email):
    """Add a Bluesky account to monitor.
    
    HANDLE is the Bluesky handle without the @ symbol (e.g., username.bsky.social)"""
    with app.app_context():
        notifier = BlueSkyNotifier(app=app)
        if not notifier.authenticate():
            console.print("[red]Failed to authenticate with Bluesky[/red]")
            return
        
        try:
            # Get account info from Bluesky
            account_info = notifier.get_account_info(handle)
            
            # Add account to database
            notification_preferences = {'desktop': desktop, 'email': email}
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
        if not notifier.authenticate():
            console.print("[red]Failed to authenticate with Bluesky[/red]")
            return
        
        accounts = list_monitored_accounts()
        if not accounts:
            console.print("[yellow]No accounts are being monitored[/yellow]")
            return
            
        for account in accounts:
            status = "[green]Active[/green]" if account.is_active else "[red]Inactive[/red]"
            prefs = {p.type: p.enabled for p in account.notification_preferences}
            console.print(f"{account.handle} ({account.display_name or 'No display name'}) - {status}")
            console.print(f"  Notifications: Desktop: {prefs.get('desktop', False)}, Email: {prefs.get('email', False)}")

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
@click.option('--email/--no-email', help='Enable/disable email notifications')
def update(handle, desktop, email):
    """Update notification preferences for a monitored account.
    
    HANDLE is the Bluesky handle without the @ symbol (e.g., username.bsky.social)"""
    with app.app_context():
        prefs = {}
        if desktop is not None:
            prefs['desktop'] = desktop
        if email is not None:
            prefs['email'] = email
            
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
@click.option('--interval', type=int, help='Check interval in seconds')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], case_sensitive=False))
def settings(interval, log_level):
    """View or update application settings.
    
    --interval: How often to check for new posts (in seconds)
    --log-level: Set logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)"""
    settings = Settings()
    if interval is not None:
        settings.update_settings({'check_interval': interval})
        console.print(f"[green]Updated check interval to {interval} seconds[/green]")
    
    if log_level is not None:
        settings.update_settings({'log_level': log_level.upper()})
        console.print(f"[green]Updated log level to {log_level.upper()}[/green]")
    
    if interval is None and log_level is None:
        # Display current settings
        console.print("\nCurrent Settings:")
        console.print(f"Check Interval: {settings.get_settings().get('check_interval', 60)} seconds")
        console.print(f"Log Level: {settings.get_settings().get('log_level', 'INFO')}")
        console.print(f"Port: {settings.get_settings().get('port', 3000)}")

@cli.command()
@click.option('-d', '--daemon', is_flag=True, help='Install and run as a system service')
def start(daemon):
    """Start the notification service.
    
    Run with --daemon to install and run as a system service (supported on macOS and Linux).
    Without --daemon, runs in the terminal and can be stopped with Ctrl+C."""
    if daemon:
        system = platform.system()
        if system == 'Darwin':  # macOS
            # Get package directory
            package_dir = os.path.dirname(os.path.dirname(__file__))
            plist_src = os.path.join(package_dir, 'services/launchd/com.bluesky-notify.plist')
            
            # Create LaunchAgents directory if it doesn't exist
            launch_agents_dir = os.path.expanduser('~/Library/LaunchAgents')
            os.makedirs(launch_agents_dir, exist_ok=True)
            
            # Copy plist file
            plist_dest = os.path.join(launch_agents_dir, 'com.bluesky-notify.plist')
            shutil.copy2(plist_src, plist_dest)
            
            # Load the service
            try:
                subprocess.run(['launchctl', 'unload', plist_dest], capture_output=True)
                subprocess.run(['launchctl', 'load', plist_dest], check=True)
                console.print("[green]Service installed and started successfully![/green]")
                console.print(f"Logs will be available at:\n- ~/Library/Logs/bluesky-notify.log\n- ~/Library/Logs/bluesky-notify.error.log")
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
            with open(service_dest, 'w') as f:
                f.write(content)
            
            # Enable and start the service
            try:
                subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
                subprocess.run(['systemctl', '--user', 'enable', 'bluesky-notify'], check=True)
                subprocess.run(['systemctl', '--user', 'start', 'bluesky-notify'], check=True)
                console.print("[green]Service installed and started successfully![/green]")
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
        notifier = BlueSkyNotifier(app=app)
        if not notifier.authenticate():
            console.print("[red]Failed to authenticate with Bluesky[/red]")
            return
        
        console.print("[green]Starting Bluesky notification service...[/green]")
        try:
            # Create and run the event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(notifier.run())
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down notification service...[/yellow]")
            notifier.stop()
            loop.close()
            sys.exit(0)
        except Exception as e:
            console.print(f"[red]Error in notification service: {e}[/red]")
            loop.close()
            sys.exit(1)
        finally:
            loop.close()

# Export the CLI function as main for the entry point
def main():
    cli()

if __name__ == '__main__':
    main()
