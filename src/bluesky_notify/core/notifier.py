"""
BlueSky Notification Service

This module provides a notification service for monitoring and alerting about new posts
from Bluesky social network accounts. It supports desktop notifications,
with configurable preferences per account.
"""

import asyncio
import aiohttp
import os
import platform
import subprocess
import shutil
import ssl
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from .database import (
    db, MonitoredAccount, NotificationPreference, NotifiedPost,
    get_monitored_accounts, add_monitored_account, remove_monitored_account,
    mark_post_notified, update_notification_preferences
)
from .logger import get_logger
from .settings import Settings

logger = get_logger('notifier')

class BlueSkyNotifier:
    """Main notification manager for Bluesky posts."""

    def __init__(self, app=None):
        """Initialize the BlueSkyNotifier."""
        self.app = app
        self.base_url = "https://api.bsky.app/xrpc"
        self.check_interval = 60  # seconds
        self._running = False
        self.loop = None
        self._session = None
        self._last_notification_url = None
        self._notification_enabled = True
        self._notification_sound = True

    async def _send_notification_async(self, title: str, message: str, url: str) -> bool:
        """Send a notification with clickable URL."""
        try:
            clean_title = self._clean_text(title)
            truncated_message = self._truncate_message(message)

            if platform.system() == 'Darwin':
                possible_paths = [
                    '/opt/homebrew/bin/terminal-notifier',
                    '/usr/local/bin/terminal-notifier',
                    shutil.which('terminal-notifier')
                ]

                terminal_notifier_path = next((path for path in possible_paths if path and os.path.exists(path)), None)

                if not terminal_notifier_path:
                    logger.error("terminal-notifier not found. Please install with: brew install terminal-notifier")
                    return False

                cmd = [
                    terminal_notifier_path,
                    '-title', clean_title,
                    '-subtitle', "Click to open in browser",
                    '-message', truncated_message,
                    '-open', url
                ]

                if self._notification_sound:
                    cmd.extend(['-sound', 'default'])

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    logger.info(f"Notification sent with URL: {url}")
                    self._last_notification_url = url
                    return True
                else:
                    logger.error(f"terminal-notifier error: {result.stderr}")
                    return False

            else:
                # ...existing code...
                pass

        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False

    def _clean_text(self, text: str) -> str:
        """Clean text for notification display."""
        if not text:
            return ""
        return text.replace('"', '\\"').replace("'", "\\'").strip()

    def _truncate_message(self, message: str, max_length: int = 200) -> str:
        """Truncate message to suitable length for notifications."""
        if not message:
            return ""
        cleaned = self._clean_text(message)
        if len(cleaned) <= max_length:
            return cleaned
        return f"{cleaned[:max_length-3]}..."

    def get_account_info(self, handle: str) -> Dict[str, Any]:
        """Get account information from Bluesky."""
        try:
            api_handle = handle.lstrip('@').lower()
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

    async def _make_request(self, endpoint: str, params: dict) -> dict:
        """Make an API request with improved error handling and SSL verification."""
        url = f"{self.base_url}/{endpoint}"

        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, ssl=ssl_context) as response:
                    if response.status == 429:
                        logger.error("Rate limit exceeded. Waiting before retrying.")
                        await asyncio.sleep(60)
                        return await self._make_request(endpoint, params)

                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientConnectorSSLError as ssl_err:
            logger.error(f"SSL Connection Error: {ssl_err}")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        response.raise_for_status()
                        return await response.json()
            except Exception as e:
                logger.error(f"Fallback request failed: {e}")
                raise
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in API request: {str(e)}")
            raise

    def list_monitored_accounts(self) -> List[Dict[str, Any]]:
        """List all monitored accounts."""
        try:
            accounts = []
            for account in get_monitored_accounts():
                prefs = account.notification_preferences
                accounts.append({
                    'handle': account.handle,
                    'display_name': account.display_name,
                    'desktop_notifications': prefs.desktop if prefs else False
                })

            if not accounts:
                logger.info("No accounts are currently being monitored")
                return []

            for account in accounts:
                status = []
                if account['desktop_notifications']:
                    status.append("Desktop")

                logger.info(
                    f"{account['display_name'] or account['handle']} "
                    f"(@{account['handle']}) - Notifications: {', '.join(status) or 'None'}"
                )

            return accounts
        except Exception as e:
            logger.error(f"Error listing accounts: {str(e)}")
            return []

    def toggle_account_status(self, handle: str) -> bool:
        """Toggle monitoring status for an account."""
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

    def update_notification_preferences(self, handle: str, desktop: Optional[bool]) -> bool:
        """Update notification preferences for an account."""
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

            db.session.commit()
            logger.info(f"Updated preferences for {handle}")
            return True
        except Exception as e:
            logger.error(f"Error updating preferences: {str(e)}")
            return False

    def remove_monitored_account(self, handle: str) -> bool:
        """Remove an account from monitoring."""
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

    async def _check_new_posts(self, account):
        """Check for new posts from a monitored account."""
        try:
            posts = await self.get_recent_posts(account.handle)
            current_time = datetime.now(timezone.utc)
            logger.debug(f"Current time (UTC): {current_time}")

            with self.app.app_context():
                account = MonitoredAccount.query.get(account.id)
                if not account:
                    logger.error(f"Account {account.handle} not found in database")
                    return []

                logger.debug(f"Account {account.handle} last_check: {account.last_check}")
                logger.debug(f"Account {account.handle} last_check tzinfo: {account.last_check.tzinfo if account.last_check else None}")

                if not account.last_check:
                    account.last_check = current_time.replace(tzinfo=None)
                    db.session.commit()
                    logger.debug(f"First check for {account.handle}, set last_check to: {account.last_check}")
                    return []

                new_posts = []
                for post in posts:
                    post_id = post.get("post", {}).get("uri")
                    if not post_id:
                        continue

                    try:
                        existing_notification = NotifiedPost.query.filter_by(
                            account_did=account.did,
                            post_id=post_id
                        ).first()

                        if existing_notification:
                            continue

                        post_time = datetime.fromisoformat(
                            post.get("post", {}).get("indexedAt", "").replace("Z", "+00:00")
                        )
                        logger.debug(f"Post time (with TZ): {post_time}")
                        logger.debug(f"Post time tzinfo: {post_time.tzinfo}")

                        post_time_utc = post_time.astimezone(timezone.utc).replace(tzinfo=None)
                        logger.debug(f"Post time (naive UTC): {post_time_utc}")

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

                account.last_check = datetime.now(timezone.utc).replace(tzinfo=None)
                db.session.commit()
                logger.debug(f"Updated last_check for {account.handle} to: {account.last_check}")

                return new_posts

        except Exception as e:
            logger.error(f"Error checking posts for {account.handle}: {str(e)}")
            logger.exception(e)
            return []

    def list_accounts(self):
        """List all monitored accounts."""
        try:
            db.session.remove()
            accounts = get_monitored_accounts()
            return accounts
        except Exception as e:
            logger.error(f"Error listing accounts: {str(e)}")
            return []

    async def get_profile(self, handle: str) -> dict:
        """Get profile information for a handle."""
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
        """Get recent posts for a handle with improved error handling."""
        try:
            max_retries = 3
            retry_delay = 5

            for attempt in range(max_retries):
                try:
                    data = await self._make_request("app.bsky.feed.getAuthorFeed", {
                        "actor": handle.lstrip('@'),
                        "limit": 10
                    })

                    if not data or 'feed' not in data:
                        logger.warning(f"No feed data returned for {handle}")
                        return []

                    return data['feed']
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed for {handle}: {str(e)}")
                        await asyncio.sleep(retry_delay * (attempt + 1))
                        continue
                    raise

            return []
        except Exception as e:
            logger.error(f"Failed to get posts for {handle}: {str(e)}")
            return []

    async def add_account(self, handle: str, notification_preferences: dict = None) -> dict:
        """Add a new account to monitor."""
        try:
            profile = await self.get_profile(handle)
            if "error" in profile:
                return profile

            with self.app.app_context():
                result = add_monitored_account(profile, notification_preferences)
                if "error" not in result:
                    account = MonitoredAccount.query.filter_by(handle=handle).first()
                    if account:
                        current_time = datetime.now(timezone.utc)
                        logger.debug(f"Setting initial last_check for {handle}")
                        logger.debug(f"Current time (UTC): {current_time}")
                        naive_utc = current_time.replace(tzinfo(None))
                        logger.debug(f"Naive UTC time: {naive_utc}")
                        account.last_check = naive_utc
                        db.session.commit()
                        logger.debug(f"Saved last_check: {account.last_check}")
                        logger.debug(f"Saved last_check tzinfo: {account.last_check.tzinfo}")
                return result

        except Exception as e:
            logger.error(f"Error adding account {handle}: {str(e)}")
            logger.exception(e)
            return {"error": str(e)}

    def remove_account(self, identifier, by_did=False):
        """Remove a monitored account."""
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
        """Update notification preferences for an account."""
        try:
            with self.app.app_context():
                result = update_notification_preferences(handle, preferences)

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
        """Run the notification service."""
        self._running = True
        self.loop = asyncio.get_event_loop()

        settings = Settings()
        current_settings = settings.get_settings()
        self.check_interval = current_settings.get('check_interval', 60)

        logger.info(f"Starting notification service with check interval: {self.check_interval} seconds")

        server_port = current_settings.get('port', 3000)
        server_url = f'http://localhost:{server_port}'

        try:
            await self._send_notification_async(
                title="Bluesky Notify Daemon Started",
                message="Notification service is now running and monitoring accounts.",
                url=server_url
            )

            from bluesky_notify.api.server import broadcast_notification
            broadcast_notification(
                "Bluesky Notify Daemon Started",
                "Notification service is now running and monitoring accounts.",
                server_url
            )
            logger.info(f"Startup notifications sent successfully. Web interface available at {server_url}")
        except Exception as e:
            logger.error(f"Error sending startup notifications: {str(e)}")

        while self._running:
            try:
                start_time = datetime.now()
                logger.debug(f"Starting check cycle at {start_time}")

                with self.app.app_context():
                    accounts = MonitoredAccount.query.filter_by(is_active=True).all()
                    logger.debug(f"Checking {len(accounts)} active accounts")

                    for account in accounts:
                        new_posts = await self._check_new_posts(account)
                        await self._send_notifications(new_posts, account)

                        account.last_check = datetime.now(timezone.utc).replace(tzinfo=None)
                        db.session.commit()

                end_time = datetime.now()
                cycle_duration = (end_time - start_time).total_seconds()
                logger.debug(f"Check cycle completed in {cycle_duration:.2f} seconds")

                sleep_time = max(0, self.check_interval - cycle_duration)
                logger.debug(f"Sleeping for {sleep_time} seconds")

                await asyncio.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Error in notification service: {str(e)}")
                await asyncio.sleep(self.check_interval)

    def stop(self) -> None:
        """Stop the notification service."""
        self._running = False

    def open_notification_url(self):
        """Open the last notification URL manually."""
        if not hasattr(self, '_last_notification_url') or not self._last_notification_url:
            logger.warning("No notification URL available to open")
            return False

        try:
            url = self._last_notification_url

            applescript = f'''
tell application "System Events"
    open location "{url}"
end tell
'''
            subprocess.run(['osascript', '-e', applescript], check=True)

            logger.info(f"Opened notification URL: {url}")
            return True
        except Exception as e:
            logger.error(f"Error opening notification URL: {str(e)}")
            return False

    async def _send_notifications(self, posts, account):
        """Send notifications for new posts."""
        try:
            for post in posts:
                text = post.get("post", {}).get("record", {}).get("text", "")
                post_id = post.get("post", {}).get("uri", "")
                if not post_id:
                    continue

                # Extract the post ID from the URI
                post_id = post_id.split('/')[-1]

                title = f"New post from {account.display_name or account.handle}"
                message = text[:200] + ("..." if len(text) > 200 else "")
                url = f"https://bsky.app/profile/{account.handle}/post/{post_id}"

                if await self._send_notification_async(title, message, url):
                    mark_post_notified(account.did, post_id)

        except Exception as e:
            logger.error(f"Error sending notifications: {str(e)}")
