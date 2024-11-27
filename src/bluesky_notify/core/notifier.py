"""
BlueSky Notification Service

This module provides a notification service for monitoring and alerting about new posts
from Bluesky social network accounts. It supports both desktop and email notifications,
with configurable preferences per account.

Features:
- Asynchronous monitoring of multiple Bluesky accounts
- Desktop notifications via system notifications
- Email notifications via configurable email service
- Customizable check intervals
- Duplicate notification prevention
- Error handling with exponential backoff
"""

import asyncio
import aiohttp
import requests
import backoff
import json
import webbrowser
import os
from desktop_notifier import DesktopNotifier
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from .database import (
    db, MonitoredAccount, NotificationPreference, NotifiedPost,
    get_monitored_accounts, add_monitored_account, remove_monitored_account,
    mark_post_notified, update_notification_preferences
)
from .logger import get_logger
from flask import current_app

logger = get_logger('notifier')

class BlueSkyNotifier:
    """Main notification manager for Bluesky posts."""
    
    def __init__(self, app=None):
        """Initialize the BlueSkyNotifier."""
        self.app = app
        self.base_url = "https://api.bsky.app/xrpc"
        self.check_interval = 60  # seconds
        self._running = False
        self.notifier = DesktopNotifier()
        self.loop = None
        self._session = None
    
    def authenticate(self) -> bool:
        """Authenticate with the Bluesky API.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            # For public API endpoints, no authentication is needed
            # Just verify we can access the API
            response = requests.get(f"{self.base_url}/app.bsky.actor.getProfile", params={"actor": "bsky.app"})
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False
    
    def get_account_info(self, handle: str) -> Dict[str, Any]:
        """Get account information from Bluesky.
        
        Args:
            handle: Account handle (e.g., @user.bsky.social)
            
        Returns:
            dict: Account information including DID, handle, and profile
            
        Raises:
            Exception: If API request fails
        """
        try:
            # Remove @ if present and convert to lowercase for API request
            api_handle = handle.lstrip('@').lower()
            
            # Get profile information
            response = requests.get(f"{self.base_url}/app.bsky.actor.getProfile", params={"actor": api_handle})
            response.raise_for_status()
            data = response.json()
            
            if not data:
                raise Exception(f"Could not find account: {handle}")
            
            return {
                'did': data.get('did'),
                'handle': data.get('handle'),
                'display_name': data.get('displayName'),
                'avatar_url': data.get('avatar'),
                'description': data.get('description', '')
            }
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            raise

    async def _make_request(self, endpoint: str, params: dict = None) -> Dict[str, Any]:
        """Make an async request to the BlueSky API with retry logic.
        
        Args:
            endpoint: API endpoint to call
            params: Optional query parameters
            
        Returns:
            dict: API response data
            
        Raises:
            aiohttp.ClientError: If API request fails
        """
        url = f"{self.base_url}/{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()

    def list_monitored_accounts(self) -> List[Dict[str, Any]]:
        """List all monitored accounts.
        
        Returns:
            list: List of monitored accounts with their status
        """
        try:
            accounts = []
            for account in get_monitored_accounts():
                prefs = account.notification_preferences
                accounts.append({
                    'handle': account.handle,
                    'display_name': account.display_name,
                    'desktop_notifications': prefs.desktop if prefs else False,
                    'email_notifications': prefs.email if prefs else False
                })
            
            if not accounts:
                logger.info("No accounts are currently being monitored")
                return []
            
            # Print account information
            for account in accounts:
                status = []
                if account['desktop_notifications']:
                    status.append("Desktop")
                if account['email_notifications']:
                    status.append("Email")
                
                logger.info(
                    f"{account['display_name'] or account['handle']} "
                    f"(@{account['handle']}) - Notifications: {', '.join(status) or 'None'}"
                )
            
            return accounts
        except Exception as e:
            logger.error(f"Error listing accounts: {str(e)}")
            return []

    def toggle_account_status(self, handle: str) -> bool:
        """Toggle monitoring status for an account.
        
        Args:
            handle: Account handle to toggle
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            account = MonitoredAccount.query.filter_by(handle=handle).first()
            if not account:
                logger.error(f"Account not found: {handle}")
                return False
            
            account.active = not account.active
            db.session.commit()
            
            status = "enabled" if account.active else "disabled"
            logger.info(f"Monitoring {status} for {handle}")
            return True
        except Exception as e:
            logger.error(f"Error toggling account status: {str(e)}")
            return False

    def update_notification_preferences(self, handle: str, desktop: Optional[bool], email: Optional[bool]) -> bool:
        """Update notification preferences for an account.
        
        Args:
            handle: Account handle to update
            desktop: Enable/disable desktop notifications
            email: Enable/disable email notifications
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            account = MonitoredAccount.query.filter_by(handle=handle).first()
            if not account:
                logger.error(f"Account not found: {handle}")
                return False
            
            prefs = account.notification_preferences
            if not prefs:
                prefs = NotificationPreference(account_id=account.id)
                db.session.add(prefs)
            
            if desktop is not None:
                prefs.desktop = desktop
            if email is not None:
                prefs.email = email
            
            db.session.commit()
            logger.info(f"Updated preferences for {handle}")
            return True
        except Exception as e:
            logger.error(f"Error updating preferences: {str(e)}")
            return False

    def remove_monitored_account(self, handle: str) -> bool:
        """Remove an account from monitoring.
        
        Args:
            handle: Account handle to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = remove_monitored_account(handle)
            if result:
                logger.info(f"Removed {handle} from monitored accounts")
            else:
                logger.error(f"Account not found: {handle}")
            return result
        except Exception as e:
            logger.error(f"Error removing account: {str(e)}")
            return False

    async def _fetch_account_info(self, identifier):
        """Fetch account information from Bluesky API.
        
        Args:
            identifier: Account handle or DID
            
        Returns:
            dict: Account information including DID, handle, and profile
            
        Raises:
            aiohttp.ClientError: If API request fails
        """
        url = f"{self.base_url}/app.bsky.actor.getProfile"
        params = {"actor": identifier}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {str(e)}")
            raise

    async def _check_new_posts(self, account):
        """Check for new posts from a monitored account.
        
        Args:
            account: MonitoredAccount instance to check
            
        Returns:
            list: New posts that haven't been notified about
        """
        try:
            posts = await self.get_recent_posts(account.handle)
            current_time = datetime.now(timezone.utc)
            logger.debug(f"Current time (UTC): {current_time}")

            with self.app.app_context():
                # Refresh account to get notification preferences within session
                account = MonitoredAccount.query.get(account.id)
                if not account:
                    logger.error(f"Account {account.handle} not found in database")
                    return []

                logger.debug(f"Account {account.handle} last_check: {account.last_check}")
                logger.debug(f"Account {account.handle} last_check tzinfo: {account.last_check.tzinfo if account.last_check else None}")

                # If this is the first check, only notify about future posts
                if not account.last_check:
                    account.last_check = current_time.replace(tzinfo=None)  # Store as naive UTC
                    db.session.commit()
                    logger.debug(f"First check for {account.handle}, set last_check to: {account.last_check}")
                    return []

                new_posts = []
                for post in posts:
                    post_id = post.get("post", {}).get("uri")
                    if not post_id:
                        continue

                    try:
                        # Check if we've already notified about this post
                        existing_notification = NotifiedPost.query.filter_by(
                            account_did=account.did,
                            post_id=post_id
                        ).first()
                        
                        if existing_notification:
                            continue

                        # Get post timestamp as UTC
                        post_time = datetime.fromisoformat(
                            post.get("post", {}).get("indexedAt", "").replace("Z", "+00:00")
                        )
                        logger.debug(f"Post time (with TZ): {post_time}")
                        logger.debug(f"Post time tzinfo: {post_time.tzinfo}")

                        # Convert to naive UTC for comparison
                        post_time_utc = post_time.astimezone(timezone.utc).replace(tzinfo=None)
                        logger.debug(f"Post time (naive UTC): {post_time_utc}")

                        # Compare naive UTC datetimes
                        logger.debug(f"Comparing post_time_utc ({post_time_utc}) > last_check ({account.last_check})")
                        if post_time_utc > account.last_check:
                            logger.debug(f"Post is newer than last check")
                            new_posts.append(post)
                        else:
                            logger.debug(f"Post is older than last check")

                    except (ValueError, TypeError, AttributeError) as e:
                        logger.error(f"Error parsing post time: {str(e)}")
                        logger.error(f"Post data: {post.get('post', {})}")
                        continue

                # Update last check time (store as naive UTC)
                account.last_check = current_time.replace(tzinfo=None)
                db.session.commit()
                logger.debug(f"Updated last_check for {account.handle} to: {account.last_check}")

                return new_posts

        except Exception as e:
            logger.error(f"Error checking posts for {account.handle}: {str(e)}")
            logger.exception(e)  # Log full traceback
            return []

    def list_accounts(self):
        """List all monitored accounts.
        
        Returns:
            list: List of monitored account data (did, handle, display_name, avatar_url)
        """
        try:
            # Ensure we're using a fresh session
            db.session.remove()
            accounts = get_monitored_accounts()
            return accounts
        except Exception as e:
            logger.error(f"Error listing accounts: {str(e)}")
            return []

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

    async def add_account(self, handle: str, notification_preferences: dict = None) -> dict:
        """Add a new account to monitor.
        
        Args:
            handle: Bluesky handle to add
            notification_preferences: Optional notification preferences (desktop, email)
            
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
                    # Set initial last_check time (store as naive UTC)
                    account = MonitoredAccount.query.filter_by(handle=handle).first()
                    if account:
                        current_time = datetime.now(timezone.utc)
                        logger.debug(f"Setting initial last_check for {handle}")
                        logger.debug(f"Current time (UTC): {current_time}")
                        naive_utc = current_time.replace(tzinfo=None)
                        logger.debug(f"Naive UTC time: {naive_utc}")
                        account.last_check = naive_utc
                        db.session.commit()
                        logger.debug(f"Saved last_check: {account.last_check}")
                        logger.debug(f"Saved last_check tzinfo: {account.last_check.tzinfo}")
                return result

        except Exception as e:
            logger.error(f"Error adding account {handle}: {str(e)}")
            logger.exception(e)  # Log full traceback
            return {"error": str(e)}

    def remove_account(self, identifier, by_did=False):
        """Remove a monitored account.
        
        Args:
            identifier: Either the handle or DID of the account to remove
            by_did: If True, identifier is treated as a DID. If False, as a handle.
            
        Returns:
            dict: Result data (success, error)
            
        Raises:
            Exception: If database operation fails
        """
        try:
            logger.info(f"Notifier removing account with {'DID' if by_did else 'handle'}: {identifier}")
            
            with self.app.app_context():
                result = remove_monitored_account(identifier, by_did)
                logger.info(f"Database removal result: {result}")
                return result

        except Exception as e:
            error_msg = f"Error removing account: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    def update_preferences(self, handle: str, preferences: dict) -> dict:
        """Update notification preferences for an account.
        
        Args:
            handle: Bluesky handle to update preferences for
            preferences: Notification preferences (desktop, email)
            
        Returns:
            dict: Result data (success, error)
            
        Raises:
            Exception: If database operation fails
        """
        try:
            with self.app.app_context():
                # Update preferences in database
                result = update_notification_preferences(handle, preferences)
                
                # Log the result
                if "error" in result:
                    logger.error(f"Error updating preferences for {handle}: {result['error']}")
                else:
                    logger.info(f"Successfully updated preferences for {handle}")
                    
                return result

        except Exception as e:
            error_msg = f"Error updating preferences: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    async def run(self) -> None:
        """Run the notification service.
        
        Continuously checks for new posts from monitored accounts and sends notifications.
        """
        self._running = True
        self.loop = asyncio.get_event_loop()
        while self._running:
            try:
                with self.app.app_context():
                    accounts = MonitoredAccount.query.filter_by(is_active=True).all()
                    for account in accounts:
                        new_posts = await self._check_new_posts(account)
                        await self._send_notifications(new_posts, account)
                        # Update last_check time (store as naive UTC)
                        account.last_check = datetime.now(timezone.utc).replace(tzinfo=None)
                        db.session.commit()
            except Exception as e:
                logger.error(f"Error in notification service: {str(e)}")

            await asyncio.sleep(self.check_interval)

    def stop(self) -> None:
        """Stop the notification service."""
        self._running = False

    async def _send_notification_async(self, title: str, message: str, url: str) -> bool:
        """Send a desktop notification using desktop-notifier asynchronously.
        
        Args:
            title: The notification title
            message: The notification message
            url: The URL to open when clicked
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        try:
            # Skip desktop notifications in Docker
            if os.getenv('DOCKER_CONTAINER'):
                logger.info("Skipping desktop notification in Docker environment")
                return True

            # Clean and truncate the message
            clean_message = message.replace('"', "'")
            truncated_message = clean_message[:140] + "..." if len(clean_message) > 140 else clean_message
            
            # Clean the title
            clean_title = title.replace('"', "'")

            # Use terminal-notifier on macOS
            if os.uname().sysname == 'Darwin':
                try:
                    os.system(f'terminal-notifier -title "{clean_title}" -message "{truncated_message}" -open "{url}"')
                    return True
                except Exception as e:
                    logger.error(f"Error using terminal-notifier: {str(e)}")
                    # Fall back to desktop-notifier if terminal-notifier fails
            
            # Use desktop-notifier for other platforms or if terminal-notifier fails
            await self.notifier.send(
                title=clean_title,
                message=truncated_message,
                on_clicked=lambda *args: webbrowser.open(url)
            )
            return True
        except Exception as e:
            logger.error(f"Unexpected error sending notification: {str(e)}")
            return False

    def _send_email(self, title: str, message: str, url: str) -> bool:
        """Send an email notification using Mailgun.
        
        Args:
            title: The email subject
            message: The email body
            url: The URL to the post
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            import requests

            # Get Mailgun configuration
            api_key = os.getenv('MAILGUN_API_KEY')
            domain = os.getenv('MAILGUN_DOMAIN')
            from_email = os.getenv('MAILGUN_FROM_EMAIL')
            to_email = os.getenv('MAILGUN_TO_EMAIL')

            if not all([api_key, domain, from_email, to_email]):
                logger.debug("Mailgun configuration not complete, skipping email notification")
                return False

            # Create HTML body with clickable link
            html = f"""
            <html>
              <body>
                <p>{message}</p>
                <p><a href="{url}">View Post</a></p>
              </body>
            </html>
            """

            # Send email using Mailgun API
            response = requests.post(
                f"https://api.mailgun.net/v3/{domain}/messages",
                auth=("api", api_key),
                data={
                    "from": from_email,
                    "to": to_email,
                    "subject": title,
                    "html": html
                }
            )
            response.raise_for_status()

            logger.info(f"Email notification sent via Mailgun: {title}")
            return True

        except Exception as e:
            logger.error(f"Error sending email notification via Mailgun: {str(e)}")
            return False

    def _format_notification(self, post, account):
        """Format post information for notification.
        
        Args:
            post: Post data from Bluesky API
            account: MonitoredAccount instance
            
        Returns:
            tuple: (title, message, url) for notification
        """
        try:
            # Get post details
            text = post.get("post", {}).get("record", {}).get("text", "")
            post_uri = post.get("post", {}).get("uri", "")
            
            # Convert URI to web URL
            if post_uri:
                try:
                    _, _, _, _, post_rkey = post_uri.split("/")
                    web_url = f"https://bsky.app/profile/{account.handle}/post/{post_rkey}"
                    
                    # Format notification title and message
                    title = f"New post from {account.display_name or account.handle}"
                    message = text[:200] + ("..." if len(text) > 200 else "")
                    
                    return title, message, web_url
                except ValueError:
                    logger.error(f"Invalid post URI format: {post_uri}")
                    return None
        except Exception as e:
            logger.error(f"Error formatting notification: {str(e)}")
            return None

    async def _send_notifications(self, new_posts, account):
        """Send notifications for new posts.
        
        Handles both desktop and email notifications based on account preferences.
        
        Args:
            new_posts: List of new posts to notify about
            account: MonitoredAccount instance
        """
        try:
            with self.app.app_context():
                # Refresh account to get notification preferences within session
                account = MonitoredAccount.query.get(account.id)
                if not account:
                    logger.error(f"Account {account.handle} not found in database")
                    return

                for post in new_posts:
                    notification = self._format_notification(post, account)
                    if not notification:
                        continue

                    title, message, url = notification

                    # Send notifications based on preferences
                    notifications_sent = False
                    for pref in account.notification_preferences:
                        if not pref.enabled:
                            continue

                        try:
                            if pref.type == "desktop":
                                desktop_sent = await self._send_notification_async(
                                    title=title,
                                    message=message,
                                    url=url
                                )
                                notifications_sent = notifications_sent or desktop_sent
                            elif pref.type == "email":
                                email_sent = self._send_email(
                                    title=title,
                                    message=message,
                                    url=url
                                )
                                notifications_sent = notifications_sent or email_sent
                        except Exception as e:
                            logger.error(f"Error sending {pref.type} notification: {str(e)}")
                            continue

                    # Only mark as notified if at least one notification was sent successfully
                    if notifications_sent:
                        mark_post_notified(account.did, post.get("post", {}).get("uri"))

        except Exception as e:
            logger.error(f"Error sending notifications for {account.handle}: {str(e)}")
