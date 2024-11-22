#!/usr/bin/env python3
import click
from rich.console import Console
from notifier import BlueSkyNotifier

console = Console()

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
    notifier = BlueSkyNotifier()
    if not notifier.authenticate():
        console.print("[red]Failed to authenticate with Bluesky[/red]")
        return
    
    try:
        # Get account info from Bluesky
        account_info = notifier.get_account_info(handle)
        
        # Add account to database
        success = notifier.db_manager.add_monitored_account(
            did=account_info['did'],
            handle=account_info['handle'],
            display_name=account_info['display_name'],
            avatar_url=account_info['avatar_url'],
            notification_preferences={'desktop': desktop, 'email': email}
        )
        
        if success:
            console.print(f"[green]Successfully added {account_info['display_name'] or handle} to monitored accounts[/green]")
        else:
            console.print("[yellow]Account is already being monitored[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error adding account: {e}[/red]")

@cli.command()
def list():
    """List all monitored accounts"""
    notifier = BlueSkyNotifier()
    if not notifier.authenticate():
        console.print("[red]Failed to authenticate with Bluesky[/red]")
        return
    
    notifier.list_monitored_accounts()

@cli.command()
@click.argument('handle')
def toggle(handle):
    """Toggle monitoring status for an account"""
    notifier = BlueSkyNotifier()
    if not notifier.authenticate():
        console.print("[red]Failed to authenticate with Bluesky[/red]")
        return

    if notifier.toggle_account_status(handle):
        console.print(f"[green]Successfully toggled monitoring status for {handle}[/green]")
    else:
        console.print(f"[red]Failed to toggle status for {handle}[/red]")

@cli.command()
@click.argument('handle')
@click.option('--desktop/--no-desktop', help='Enable/disable desktop notifications')
@click.option('--email/--no-email', help='Enable/disable email notifications')
def update(handle, desktop, email):
    """Update notification preferences for an account"""
    if desktop is None and email is None:
        console.print("[yellow]No preferences specified. Use --desktop/--no-desktop or --email/--no-email[/yellow]")
        return

    notifier = BlueSkyNotifier()
    if not notifier.authenticate():
        console.print("[red]Failed to authenticate with Bluesky[/red]")
        return

    if notifier.update_notification_preferences(handle, desktop, email):
        console.print(f"[green]Successfully updated preferences for {handle}[/green]")
    else:
        console.print(f"[red]Failed to update preferences for {handle}[/red]")

@cli.command()
@click.argument('handle')
def remove(handle):
    """Remove an account from monitoring"""
    notifier = BlueSkyNotifier()
    if not notifier.authenticate():
        console.print("[red]Failed to authenticate with Bluesky[/red]")
        return

    if notifier.remove_monitored_account(handle):
        console.print(f"[green]Successfully removed {handle} from monitored accounts[/green]")
    else:
        console.print(f"[red]Failed to remove {handle}[/red]")

@cli.command()
def start():
    """Start the notification service"""
    console.print("[yellow]Starting Bluesky notification service...[/yellow]")
    console.print("[yellow]Press Ctrl+C to stop[/yellow]")
    
    notifier = BlueSkyNotifier()
    if not notifier.authenticate():
        console.print("[red]Failed to authenticate with Bluesky[/red]")
        return
    
    try:
        notifier.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping notification service...[/yellow]")

if __name__ == '__main__':
    cli()
