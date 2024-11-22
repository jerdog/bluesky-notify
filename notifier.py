"""
BlueSky Notification Manager

This module handles the core notification functionality for BlueSky accounts.
"""

import os
import time
import logging
from datetime import datetime
from atproto import Client, models
from desktop_notifier import DesktopNotifier, Notification
from database import DatabaseManager

logger = logging.getLogger(__name__)

class BlueSkyNotifier:
    """Manages notifications for BlueSky accounts"""
    
    def __init__(self):
        """Initialize the notifier with database and notification handlers"""
        self.db_manager = DatabaseManager()
        self.desktop_notifier = DesktopNotifier()
        self.client = None
        self.running = False
        self._authenticated = False

    def authenticate(self):
        """Authenticate with BlueSky using environment variables"""
        try:
            username = os.getenv('BLUESKY_USERNAME')
            password = os.getenv('BLUESKY_PASSWORD')
            
            if not username or not password:
                logger.error("BlueSky credentials not found in environment variables")
                return False
            
            self.client = Client()
            self.client.login(username, password)
            logger.info("Successfully authenticated with BlueSky")
            self._authenticated = True
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            self._authenticated = False
            return False

    def get_account_info(self, handle):
        """Get account information from BlueSky"""
        try:
            # Remove @ if present
            handle = handle.lstrip('@')
            response = self.client.get_profile(handle)
            return {
                'did': response.did,
                'handle': response.handle,
                'display_name': response.display_name,
                'avatar_url': response.avatar
            }
        except Exception as e:
            logger.error(f"Error getting account info for {handle}: {e}")
            raise

    async def send_notification(self, title, message):
        """Send a desktop notification"""
        try:
            notification = Notification(
                title=title,
                message=message
            )
            await self.desktop_notifier.send_notification(notification)
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    def check_new_posts(self):
        """Check for new posts from monitored accounts"""
        try:
            accounts = self.db_manager.get_monitored_accounts()
            
            for account in accounts:
                if not account['is_active']:
                    continue
                    
                # Get recent posts
                response = self.client.get_author_feed(account['did'])
                
                for post in response.feed:
                    # Skip if we've already notified about this post
                    if self.db_manager.is_post_notified(account['did'], post.post.uri):
                        continue
                    
                    # Create notification
                    title = f"New post from {account['display_name'] or account['handle']}"
                    message = post.post.record.text[:200] + "..." if len(post.post.record.text) > 200 else post.post.record.text
                    
                    # Send desktop notification if enabled
                    if account['notification_preferences'].get('desktop', True):
                        import asyncio
                        asyncio.run(self.send_notification(title, message))
                    
                    # Mark post as notified
                    self.db_manager.mark_post_notified(account['did'], post.post.uri)
                    
        except Exception as e:
            logger.error(f"Error checking new posts: {e}")

    def run(self):
        """Start monitoring for new posts"""
        self.running = True
        logger.info("Starting BlueSky notification monitor")
        
        while self.running:
            try:
                self.check_new_posts()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in notification loop: {e}")
                time.sleep(60)  # Wait before retrying

    def stop(self):
        """Stop monitoring for new posts"""
        self.running = False
        logger.info("Stopping BlueSky notification monitor")
