"""
BlueSky Notification Service

This module provides notifications for Bluesky social network posts.
"""

import asyncio
import requests
import backoff
import json
import webbrowser
import os
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

class BlueSkyNotifier:
    """Main notification manager for Bluesky posts.
    
    This class handles the monitoring of Bluesky accounts and sends notifications
    for new posts using macOS notifications.
    
    Attributes:
        app: Flask application instance
        base_url: Base URL for the Bluesky API
        check_interval: Time between checks for new posts (in seconds)
        _running: Flag indicating if the monitor is running
        last_check: Dictionary tracking last check time per account
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

    def _send_notification(self, title: str, message: str, url: str) -> bool:
        """Send a macOS notification using terminal-notifier.
        
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
            # Clean and truncate the message
            # Remove quotes and escape special characters
            clean_message = message.replace('"', "'").replace('[', r'\[').replace(']', r'\]')
            # Truncate to a reasonable length to avoid issues
            truncated_message = clean_message[:140] + "..." if len(clean_message) > 140 else clean_message
            
            # Clean the title similarly
            clean_title = title.replace('"', "'").replace('[', r'\[').replace(']', r'\]')

            subprocess.run([
                'terminal-notifier',
                '-title', clean_title,
                '-message', truncated_message,
                '-open', url,
                '-sound', 'default',
                '-group', 'com.blueskynotify'
            ], check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error sending notification: {str(e)}\nOutput: {e.stdout}\nError: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending notification: {str(e)}")
            return False

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
