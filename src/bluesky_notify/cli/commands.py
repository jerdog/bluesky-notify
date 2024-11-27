#!/usr/bin/env python3
import click
import os
from rich.console import Console
from flask import Flask
from bluesky_notify.core.notifier import BlueSkyNotifier
from bluesky_notify.core.settings import Settings
from bluesky_notify.core.database import db, add_monitored_account, list_monitored_accounts, toggle_account_status, update_notification_preferences, remove_monitored_account
from bluesky_notify.core.config import Config, get_data_dir
import asyncio

console = Console()

# Initialize Flask app
app = Flask(__name__)

# Load config
config = Config()

# Ensure data directory exists and set database path
data_dir = get_data_dir()
os.makedirs(data_dir, exist_ok=True)
db_path = os.path.join(data_dir, 'bluesky_notify.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

@click.group()
def cli():
    """Bluesky Notification Manager - Track and receive notifications from Bluesky accounts"""
    pass

@cli.command()
@click.argument('handle')
@click.option('--desktop/--no-desktop', default=True, help='Enable/disable desktop notifications')
@click.option('--email/--no-email', default=False, help='Enable/disable email notifications')
def add(handle, desktop, email):
    """Add a new account to monitor"""
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
    """List all monitored accounts"""
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
    """Toggle monitoring status for an account"""
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
    """Update notification preferences for an account"""
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
    """Remove an account from monitoring"""
    with app.app_context():
        if remove_monitored_account(handle):
            console.print(f"[green]Successfully removed {handle} from monitored accounts[/green]")
        else:
            console.print(f"[red]Failed to remove {handle}[/red]")

@cli.command()
@click.option('--interval', type=int, help='Check interval in seconds')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], case_sensitive=False))
def settings(interval, log_level):
    """View or update application settings"""
    settings = Settings()
    current_settings = settings.get_settings()
    
    if interval is not None:
        settings.update_settings({'check_interval': interval})
        console.print(f"[green]Updated check interval to {interval} seconds[/green]")
    
    if log_level is not None:
        settings.update_settings({'log_level': log_level.upper()})
        console.print(f"[green]Updated log level to {log_level.upper()}[/green]")
    
    if interval is None and log_level is None:
        # Display current settings
        console.print("\nCurrent Settings:")
        console.print(f"Check Interval: {current_settings.get('check_interval', 60)} seconds")
        console.print(f"Log Level: {current_settings.get('log_level', 'INFO')}")
        console.print(f"Port: {current_settings.get('port', 3000)}")

@cli.command()
def start():
    """Start the notification service"""
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
        except Exception as e:
            console.print(f"[red]Error in notification service: {e}[/red]")
        finally:
            loop.close()

# Export the CLI function as main for the entry point
def main():
    cli()

if __name__ == '__main__':
    main()
