"""
BlueSky Notification Service

This module provides a cross-platform notification system for Bluesky social network posts.
It supports native notifications on macOS, Linux, and Windows, with a fallback console
output for unsupported platforms.

The notification system is designed to:
1. Show notifications for new posts
2. Support click-to-open functionality
3. Use native notification systems where possible
4. Provide consistent behavior across platforms

Classes:
    NotificationHandler: Factory class for platform-specific notifiers
    MacOSNotifier: Handles notifications on macOS using terminal-notifier
    LinuxNotifier: Handles notifications on Linux using notify-send
    WindowsNotifier: Handles notifications on Windows using Toast Notifications
    FallbackNotifier: Provides console output for unsupported platforms
    BlueSkyNotifier: Main notification manager for Bluesky posts
"""

import asyncio
import requests
import backoff
import json
import webbrowser
import os
import sys
import platform
import subprocess
from datetime import datetime, timezone
from .database import (
    db, MonitoredAccount, NotificationPreference, NotifiedPost,
    get_monitored_accounts, add_monitored_account, remove_monitored_account,
    mark_post_notified
)
from .logger import get_logger
from flask import current_app

logger = get_logger('notifier')

class NotificationHandler:
    """Factory class for creating platform-specific notification handlers.
    
    This class determines the appropriate notification handler based on the user's
    operating system. It supports macOS, Linux, and Windows, with a fallback for
    other platforms.
    """
    
    @staticmethod
    def get_handler():
        """Get the appropriate notification handler for the current platform.
        
        Returns:
            A platform-specific notifier instance that implements the send_notification method.
            - MacOSNotifier for macOS
            - LinuxNotifier for Linux
            - WindowsNotifier for Windows
            - FallbackNotifier for other platforms
        """
        system = platform.system().lower()
        if system == 'darwin':
            return MacOSNotifier()
        elif system == 'linux':
            return LinuxNotifier()
        elif system == 'windows':
            return WindowsNotifier()
        else:
            return FallbackNotifier()

class MacOSNotifier:
    """macOS notification handler using terminal-notifier.
    
    This class uses the terminal-notifier command-line tool to show native macOS
    notifications with click-to-open functionality.
    
    Requirements:
        terminal-notifier must be installed (brew install terminal-notifier)
    """
    
    def send_notification(self, title: str, message: str, url: str) -> bool:
        """Send a native macOS notification.
        
        Args:
            title: The notification title (usually the author's name)
            message: The notification message (usually the post content)
            url: The URL to open when the notification is clicked
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
            
        Raises:
            subprocess.CalledProcessError: If terminal-notifier command fails
        """
        try:
            subprocess.run([
                'terminal-notifier',
                '-title', title,
                '-message', message,
                '-open', url,
                '-sound', 'default',
                '-group', 'com.blueskynotify'
            ], check=True)
            return True
        except Exception as e:
            logger.error(f"Error sending macOS notification: {str(e)}")
            return False

class LinuxNotifier:
    """Linux notification handler using notify-send.
    
    This class uses the notify-send command and creates a desktop entry to handle
    notification clicks. It stores the current URL in a cache file that is read
    when the notification is clicked.
    
    Requirements:
        notify-send (usually pre-installed, part of libnotify-bin)
    """
    
    def send_notification(self, title: str, message: str, url: str) -> bool:
        """Send a native Linux notification.
        
        Args:
            title: The notification title (usually the author's name)
            message: The notification message (usually the post content)
            url: The URL to open when the notification is clicked
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
            
        Notes:
            Creates a desktop entry on first run to handle notification clicks.
            Stores the URL in a cache file that is read when notification is clicked.
        """
        try:
            # Store URL for click handling
            url_file = os.path.expanduser('~/.cache/bluesky_notify_url')
            with open(url_file, 'w') as f:
                f.write(url)
            
            # Create notification with action
            subprocess.run([
                'notify-send',
                title,
                message,
                '--action=default=Open Post',
                '--hint=string:desktop-entry:bluesky-notify'
            ], check=True)
            
            # Set up URL handler (needs to be done once during setup)
            handler_path = os.path.expanduser('~/.local/share/applications/bluesky-notify.desktop')
            if not os.path.exists(handler_path):
                handler_content = f"""[Desktop Entry]
Type=Application
Name=Bluesky Notify
Exec=xdg-open $(cat ~/.cache/bluesky_notify_url)
Terminal=false
"""
                os.makedirs(os.path.dirname(handler_path), exist_ok=True)
                with open(handler_path, 'w') as f:
                    f.write(handler_content)
            
            return True
        except Exception as e:
            logger.error(f"Error sending Linux notification: {str(e)}")
            return False

class WindowsNotifier:
    """Windows notification handler using Windows Toast Notifications.
    
    This class creates interactive toast notifications using PowerShell commands.
    The notifications include an "Open Post" button that opens the URL when clicked.
    
    Requirements:
        Windows 10 or later (uses built-in Toast Notifications)
    """
    
    def send_notification(self, title: str, message: str, url: str) -> bool:
        """Send a native Windows toast notification.
        
        Args:
            title: The notification title (usually the author's name)
            message: The notification message (usually the post content)
            url: The URL to open when the notification is clicked
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
            
        Notes:
            Creates an interactive toast notification with an "Open Post" button.
            Uses PowerShell commands to create and show the notification.
        """
        try:
            # Using powershell to create and show a toast notification
            script = f"""
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

            $template = @"
            <toast>
                <visual>
                    <binding template="ToastText02">
                        <text id="1">{title}</text>
                        <text id="2">{message}</text>
                    </binding>
                </visual>
                <actions>
                    <action content="Open Post" arguments="{url}" activationType="protocol"/>
                </actions>
            </toast>
"@

            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($template)
            $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Bluesky Notify").Show($toast)
            """
            
            subprocess.run(['powershell', '-Command', script], check=True)
            return True
        except Exception as e:
            logger.error(f"Error sending Windows notification: {str(e)}")
            return False

class FallbackNotifier:
    """Fallback notification handler using console output.
    
    This class provides a simple console-based notification system for platforms
    where native notifications are not supported or configured.
    """
    
    def send_notification(self, title: str, message: str, url: str) -> bool:
        """Print notification information to the console.
        
        Args:
            title: The notification title (usually the author's name)
            message: The notification message (usually the post content)
            url: The URL to the post
            
        Returns:
            bool: True if message was printed successfully, False otherwise
        """
        try:
            print(f"\n{'='*50}")
            print(f"New Bluesky Post!")
            print(f"Title: {title}")
            print(f"Message: {message}")
            print(f"URL: {url}")
            print(f"{'='*50}\n")
            return True
        except Exception as e:
            logger.error(f"Error sending fallback notification: {str(e)}")
            return False

class BlueSkyNotifier:
    """Main notification manager for Bluesky posts.
    
    This class handles the monitoring of Bluesky accounts and sends notifications
    for new posts using the appropriate platform-specific notification system.
    
    Attributes:
        app: Flask application instance
        base_url: Base URL for the Bluesky API
        check_interval: Time between checks for new posts (in seconds)
        _running: Flag indicating if the monitor is running
        last_check: Dictionary tracking last check time per account
        notifier: Platform-specific notification handler instance
    """
    
    def __init__(self, app=None):
        """Initialize the BlueSkyNotifier.
        
        Args:
            app: Optional Flask application instance
        """
        self.app = app
        self.base_url = "https://public.api.bsky.app/xrpc"
        self.check_interval = 60  # seconds
        self._running = False
        self.last_check = {}
        self.notifier = NotificationHandler.get_handler()

    def _send_macos_notification(self, title: str, message: str, url: str) -> bool:
        """Send a native macOS notification using terminal-notifier.
        
        Args:
            title: The notification title
            message: The notification message
            url: The URL to open when clicked
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
            
        Raises:
            subprocess.CalledProcessError: If terminal-notifier command fails
        """
        try:
            subprocess.run([
                'terminal-notifier',
                '-title', title,
                '-message', message,
                '-open', url,
                '-sound', 'default',
                '-group', 'com.blueskynotify'
            ], check=True)
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False

    def _send_notification(self, title: str, message: str, url: str) -> bool:
        """Send a platform-specific notification.
        
        Args:
            title: The notification title
            message: The notification message
            url: The URL to open when clicked
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        return self.notifier.send_notification(title, message, url)

    @backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
    async def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """Make a request to the BlueSky API with retry logic.
        
        Args:
            endpoint: API endpoint to call
            params: Optional query parameters
            
        Returns:
            dict: API response data
            
        Raises:
            requests.exceptions.RequestException: If API request fails
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise

    async def get_profile(self, handle: str) -> dict:
        """Get profile information for a handle.
        
        Args:
            handle: Bluesky handle to retrieve profile for
            
        Returns:
            dict: Profile data (did, handle, display_name, avatar_url, description)
            
        Raises:
            Exception: If API request fails
        """
        try:
            data = await self._make_request("app.bsky.actor.getProfile", {"actor": handle})
            return {
                "did": data.get("did"),
                "handle": data.get("handle"),
                "display_name": data.get("displayName", handle),
                "avatar_url": data.get("avatar"),
                "description": data.get("description", "")
            }
        except Exception as e:
            logger.error(f"Failed to get profile for {handle}: {str(e)}")
            return {"error": str(e)}

    async def get_recent_posts(self, handle: str) -> list:
        """Get recent posts for a handle.
        
        Args:
            handle: Bluesky handle to retrieve posts for
            
        Returns:
            list: List of recent post data (post_id, post_time, text, url)
            
        Raises:
            Exception: If API request fails
        """
        try:
            data = await self._make_request("app.bsky.feed.getAuthorFeed", {"actor": handle})
            return data.get("feed", [])
        except Exception as e:
            logger.error(f"Failed to get posts for {handle}: {str(e)}")
            return []

    def list_accounts(self) -> list:
        """List all monitored accounts.
        
        Returns:
            list: List of monitored account data (did, handle, display_name, avatar_url)
        """
        with self.app.app_context():
            return get_monitored_accounts()

    async def add_account(self, handle: str, notification_preferences: dict = None) -> dict:
        """Add a new account to monitor.
        
        Args:
            handle: Bluesky handle to add
            notification_preferences: Optional notification preferences (desktop, mobile)
            
        Returns:
            dict: Result data (success, error)
            
        Raises:
            Exception: If API request fails
        """
        try:
            # Verify account exists
            profile = await self.get_profile(handle)
            if "error" in profile:
                return profile

            # Add account to database
            with self.app.app_context():
                result = add_monitored_account(profile, notification_preferences)
            if "error" not in result:
                self.last_check[handle] = datetime.now(timezone.utc)
            return result

        except Exception as e:
            logger.error(f"Error adding account {handle}: {str(e)}")
            return {"error": str(e)}

    def remove_account(self, handle: str) -> dict:
        """Remove a monitored account.
        
        Args:
            handle: Bluesky handle to remove
            
        Returns:
            dict: Result data (success, error)
            
        Raises:
            Exception: If database operation fails
        """
        try:
            with self.app.app_context():
                result = remove_monitored_account(handle)
            if "error" not in result:
                self.last_check.pop(handle, None)
            return result

        except Exception as e:
            logger.error(f"Error removing account {handle}: {str(e)}")
            return {"error": str(e)}

    def update_preferences(self, handle: str, preferences: dict) -> dict:
        """Update notification preferences for an account.
        
        Args:
            handle: Bluesky handle to update preferences for
            preferences: Notification preferences (desktop, mobile)
            
        Returns:
            dict: Result data (success, error)
            
        Raises:
            Exception: If database operation fails
        """
        try:
            with self.app.app_context():
                account = MonitoredAccount.query.filter_by(handle=handle).first()
                if not account:
                    return {"error": "Account not found"}

                # Update preferences
                for pref in account.notification_preferences:
                    if pref.type in preferences:
                        pref.enabled = preferences[pref.type]
                
                # Add any new preferences
                for pref_type, enabled in preferences.items():
                    if not any(p.type == pref_type for p in account.notification_preferences):
                        new_pref = NotificationPreference(
                            account=account,
                            type=pref_type,
                            enabled=enabled
                        )
                        db.session.add(new_pref)

                db.session.commit()
                return {"message": "Preferences updated successfully"}

        except Exception as e:
            logger.error(f"Error updating preferences for {handle}: {str(e)}")
            return {"error": str(e)}

    async def check_new_posts(self, account: MonitoredAccount) -> None:
        """Check for new posts from an account and send notifications.
        
        Args:
            account: MonitoredAccount instance to check for new posts
            
        Raises:
            Exception: If API request fails
        """
        try:
            posts = await self.get_recent_posts(account.handle)
            last_check = self.last_check.get(account.handle)

            with self.app.app_context():
                # Refresh account to get notification preferences within session
                account = MonitoredAccount.query.get(account.id)
                if not account:
                    logger.error(f"Account {account.handle} not found in database")
                    return

                for post in posts:
                    post_id = post.get("post", {}).get("uri")
                    if not post_id:
                        continue

                    # Check if we've already notified about this post
                    if NotifiedPost.query.filter_by(
                        account_did=account.did,
                        post_id=post_id
                    ).first():
                        continue

                    # Get post timestamp
                    post_time = datetime.fromisoformat(
                        post.get("post", {}).get("indexedAt", "").replace("Z", "+00:00")
                    )

                    # Skip if post is older than last check
                    if last_check and post_time <= last_check:
                        continue

                    # Send notifications based on preferences
                    text = post.get("post", {}).get("record", {}).get("text", "")
                    post_uri = post.get("post", {}).get("uri", "")
                    
                    # Convert URI to web URL
                    # Format: at://did:plc:XXX/app.bsky.feed.post/YYY -> https://bsky.app/profile/handle/post/YYY
                    if post_uri:
                        try:
                            _, _, _, _, post_rkey = post_uri.split("/")
                            web_url = f"https://bsky.app/profile/{account.handle}/post/{post_rkey}"
                            
                            for pref in account.notification_preferences:
                                if not pref.enabled:
                                    continue

                                if pref.type == "desktop":
                                    self._send_notification(
                                        title=f"New post from {account.display_name or account.handle}",
                                        message=text[:200] + ("..." if len(text) > 200 else ""),
                                        url=web_url
                                    )

                        except ValueError:
                            logger.error(f"Invalid post URI format: {post_uri}")
                            continue

                    # Mark as notified
                    mark_post_notified(account.did, post_id)

        except Exception as e:
            logger.error(f"Error checking posts for {account.handle}: {str(e)}")

    async def run(self) -> None:
        """Run the notification service.
        
        Continuously checks for new posts from monitored accounts and sends notifications.
        """
        self._running = True
        while self._running:
            try:
                with self.app.app_context():
                    accounts = MonitoredAccount.query.filter_by(is_active=True).all()
                    for account in accounts:
                        await self.check_new_posts(account)
                        self.last_check[account.handle] = datetime.now(timezone.utc)
            except Exception as e:
                logger.error(f"Error in notification service: {str(e)}")

            await asyncio.sleep(self.check_interval)

    def stop(self) -> None:
        """Stop the notification service."""
        self._running = False
