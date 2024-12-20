"""
Database models and operations for the BlueSky notification system.

This module provides the database models and operations for managing monitored accounts,
notification preferences, and notification history. It uses SQLAlchemy as the ORM and
supports SQLite as the database backend.

Models:
- MonitoredAccount: Stores information about Bluesky accounts being monitored
- NotificationPreference: Stores notification settings per account
- NotifiedPost: Tracks which posts have been notified about to prevent duplicates

The module also provides helper functions for common database operations like
adding/removing accounts and marking posts as notified.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, joinedload
import logging

logger = logging.getLogger(__name__)

db = SQLAlchemy()

class MonitoredAccount(db.Model):
    """Account model for storing BlueSky account information.

    Attributes:
        id: Primary key
        did: Decentralized identifier for the account
        handle: Account handle (username)
        avatar_url: URL to account avatar image
        display_name: Display name of the account
        is_active: Whether the account is currently being monitored
        created_at: When the account was added to monitoring
        updated_at: When the account was last updated
        last_check: When we last checked for posts
        notification_preferences: Related NotificationPreference objects
    """
    __tablename__ = 'monitored_accounts'

    id = Column(Integer, primary_key=True)
    did = Column(String, unique=True)
    handle = Column(String)
    avatar_url = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_check = Column(DateTime, nullable=True)  # Track when we last checked for posts
    notification_preferences = relationship(
        'NotificationPreference',
        back_populates='account',
        cascade='all, delete-orphan'
    )

    def to_dict(self):
        """Convert the account to a dictionary for JSON serialization.

        Returns:
            dict: Account data in dictionary format
        """
        # Create a dictionary of notification preferences
        preferences = {}
        for pref in self.notification_preferences:
            preferences[pref.type] = pref.enabled

        return {
            'id': self.id,
            'did': self.did,
            'handle': self.handle,
            'display_name': self.display_name,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'notification_preferences': preferences
        }

class NotificationPreference(db.Model):
    """Notification preferences for accounts.

    Attributes:
        id: Primary key
        account_id: Foreign key to MonitoredAccount
        type: Type of notification ('desktop')
        enabled: Whether this notification type is enabled
        account: Related MonitoredAccount object
    """
    __tablename__ = 'notification_preferences'

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('monitored_accounts.id'))
    type = Column(String)  # 'desktop'
    enabled = Column(Boolean, default=True)
    account = relationship('MonitoredAccount', back_populates='notification_preferences')

class NotifiedPost(db.Model):
    """Record of posts that have been notified about.

    Attributes:
        id: Primary key
        account_did: DID of the account the post belongs to
        post_id: ID of the post that was notified about
        notified_at: When the notification was sent
    """
    __tablename__ = 'notified_posts'

    id = Column(Integer, primary_key=True)
    account_did = Column(String)
    post_id = Column(String)
    notified_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('account_did', 'post_id', name='uq_account_post'),
    )

def add_monitored_account(profile_data, notification_preferences=None):
    """Add a new monitored account.

    Args:
        profile_data (dict): Account profile data containing did, handle, etc.
        notification_preferences (dict, optional): Dict of notification preferences

    Returns:
        dict: Result data with account info or error message
    """
    try:
        # Check if account already exists
        existing = MonitoredAccount.query.filter_by(did=profile_data['did']).first()
        if existing:
            return {"error": f"Account {profile_data['handle']} already exists"}

        # Create new account
        account = MonitoredAccount(
            did=profile_data['did'],
            handle=profile_data['handle'],
            display_name=profile_data.get('display_name'),
            avatar_url=profile_data.get('avatar_url'),
            is_active=True
        )

        # Add notification preferences
        if notification_preferences:
            for pref_type, enabled in notification_preferences.items():
                pref = NotificationPreference(
                    type=pref_type,
                    enabled=enabled
                )
                account.notification_preferences.append(pref)

        db.session.add(account)
        db.session.commit()

        return {"message": "Account added successfully", "account": account.to_dict()}

    except Exception as e:
        logger.error(f"Error adding monitored account: {e}")
        db.session.rollback()
        return {"error": f"Error adding account: {str(e)}"}

def get_monitored_accounts():
    """Get all monitored accounts with their preferences.

    Returns:
        list: List of MonitoredAccount objects with loaded preferences
    """
    try:
        accounts = MonitoredAccount.query.options(
            joinedload(MonitoredAccount.notification_preferences)
        ).all()
        return accounts
    except Exception as e:
        logger.error(f"Error fetching monitored accounts: {e}")
        return []

def list_monitored_accounts():
    """List all monitored accounts with their preferences.

    Returns:
        list: List of MonitoredAccount objects with loaded preferences
    """
    try:
        accounts = MonitoredAccount.query.options(
            joinedload(MonitoredAccount.notification_preferences)
        ).all()
        return accounts
    except Exception as e:
        logger.error(f"Error listing monitored accounts: {e}")
        return []

def toggle_account_status(handle):
    """Toggle monitoring status for an account.

    Args:
        handle (str): Account handle to toggle

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        account = MonitoredAccount.query.filter_by(handle=handle).first()
        if not account:
            return False

        account.is_active = not account.is_active
        db.session.commit()
        return True

    except Exception as e:
        logger.error(f"Error toggling account status: {e}")
        db.session.rollback()
        return False

def update_notification_preferences(handle, preferences):
    """Update notification preferences for an account.

    Args:
        handle (str): Account handle to update
        preferences (dict): Dict of notification preferences (e.g., {'desktop': True})

    Returns:
        dict: Result data with account info or error message
    """
    try:
        logger.info(f"Updating preferences for {handle} with {preferences}")

        # Ensure we're using a fresh session
        db.session.remove()

        account = MonitoredAccount.query.filter_by(handle=handle).first()
        if not account:
            logger.error(f"Account not found: {handle}")
            return {"error": "Account not found"}

        logger.info(f"Current preferences for {handle}: {[{'type': p.type, 'enabled': p.enabled} for p in account.notification_preferences]}")

        # Update existing preferences
        updated = False
        for pref in account.notification_preferences:
            if pref.type in preferences:
                old_value = pref.enabled
                pref.enabled = preferences[pref.type]
                logger.info(f"Updating {pref.type} preference for {handle}: {old_value} -> {pref.enabled}")
                updated = True
                db.session.add(pref)

        # Add any missing preferences
        existing_types = {pref.type for pref in account.notification_preferences}
        for pref_type, enabled in preferences.items():
            if pref_type not in existing_types:
                logger.info(f"Adding new {pref_type} preference for {handle}: {enabled}")
                new_pref = NotificationPreference(
                    account=account,
                    type=pref_type,
                    enabled=enabled
                )
                db.session.add(new_pref)
                updated = True

        if not updated:
            logger.warning(f"No preferences were updated for {handle}")

        # Commit changes and refresh account
        db.session.commit()
        db.session.refresh(account)

        logger.info(f"Updated preferences for {handle}: {[{'type': p.type, 'enabled': p.enabled} for p in account.notification_preferences]}")

        return {
            "message": "Preferences updated successfully",
            "account": account.to_dict()
        }

    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        db.session.rollback()
        return {"error": str(e)}

def remove_monitored_account(identifier, by_did=False):
    """Remove a monitored account.

    Args:
        identifier (str): Account handle or DID to remove
        by_did (bool): If True, identifier is treated as a DID. If False, as a handle.

    Returns:
        dict: Result data with account info or error message
    """
    try:
        if by_did:
            account = MonitoredAccount.query.filter_by(did=identifier).first()
        else:
            account = MonitoredAccount.query.filter_by(handle=identifier).first()

        if not account:
            return {"error": f"Account not found with {'DID' if by_did else 'handle'}: {identifier}"}

        # Store account info before deletion for return value
        account_info = account.to_dict()

        # Delete the account
        db.session.delete(account)
        db.session.commit()

        return {"message": "Account removed successfully", "account": account_info}

    except Exception as e:
        logger.error(f"Error removing monitored account: {e}")
        db.session.rollback()
        return {"error": f"Error removing account: {str(e)}"}

def mark_post_notified(account_did: str, post_id: str) -> bool:
    """Mark a post as having been notified about.

    Args:
        account_did: The DID of the account
        post_id: The ID of the post

    Returns:
        bool: True if post was marked as notified, False if already notified
    """
    try:
        # Try to insert directly - this is more efficient and handles race conditions
        notification = NotifiedPost(
            account_did=account_did,
            post_id=post_id
        )
        db.session.add(notification)
        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()
        # Check if this was a unique constraint violation
        if isinstance(e, db.exc.IntegrityError) and "UNIQUE constraint failed" in str(e):
            # This is expected when the post was already notified about
            return False
        # Log other unexpected errors
        logger.error(f"Error marking post as notified: {str(e)}")
        return False

def init_db(app):
    """Initialize the database with the Flask app context.

    Args:
        app: Flask application instance
    """
    with app.app_context():
        db.init_app(app)
        db.create_all()
