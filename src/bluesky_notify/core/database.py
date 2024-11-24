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
import os

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
    notification_preferences = relationship(
        'NotificationPreference',
        back_populates='account',
        cascade='all, delete-orphan'
    )

class NotificationPreference(db.Model):
    """Notification preferences for accounts.
    
    Attributes:
        id: Primary key
        account_id: Foreign key to MonitoredAccount
        type: Type of notification ('desktop' or 'email')
        enabled: Whether this notification type is enabled
        account: Related MonitoredAccount object
    """
    __tablename__ = 'notification_preferences'

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('monitored_accounts.id'))
    type = Column(String)  # 'desktop' or 'email'
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

def get_monitored_accounts():
    """Get all monitored accounts with their preferences.
    
    Returns:
        list: List of MonitoredAccount objects with loaded preferences
    """
    try:
        return MonitoredAccount.query.options(
            joinedload(MonitoredAccount.notification_preferences)
        ).all()
    except Exception as e:
        logger.error(f"Error fetching monitored accounts: {str(e)}")
        return []

def add_monitored_account(account_info, notification_preferences=None):
    """Add a new monitored account.
    
    Args:
        account_info: Dict containing account information (did, handle, etc.)
        notification_preferences: Optional list of notification preferences
        
    Returns:
        dict: Result of the operation
    """
    try:
        # Check if account already exists
        existing = MonitoredAccount.query.filter_by(did=account_info['did']).first()
        if existing:
            return {"error": "Account already being monitored"}

        # Create new account
        account = MonitoredAccount(
            did=account_info['did'],
            handle=account_info['handle'],
            avatar_url=account_info.get('avatar_url'),
            display_name=account_info.get('display_name')
        )

        # Add default notification preferences if none provided
        if not notification_preferences:
            notification_preferences = [
                {"type": "desktop", "enabled": True},
                {"type": "email", "enabled": False}
            ]

        # Add notification preferences
        for pref in notification_preferences:
            account.notification_preferences.append(
                NotificationPreference(
                    type=pref['type'],
                    enabled=pref['enabled']
                )
            )

        db.session.add(account)
        db.session.commit()

        return {"success": True, "account": account}

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding monitored account: {str(e)}")
        return {"error": str(e)}

def remove_monitored_account(identifier, by_did=False):
    """Remove a monitored account.
    
    Args:
        identifier: Either the handle or DID of the account to remove
        by_did: If True, identifier is treated as a DID. If False, as a handle.
        
    Returns:
        dict: Result of the operation
    """
    try:
        # Find account
        if by_did:
            account = MonitoredAccount.query.filter_by(did=identifier).first()
        else:
            account = MonitoredAccount.query.filter_by(handle=identifier).first()

        if not account:
            return {"error": "Account not found"}

        # Remove account and its preferences
        db.session.delete(account)
        db.session.commit()

        return {"success": True}

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing monitored account: {str(e)}")
        return {"error": str(e)}

def mark_post_notified(account_did: str, post_id: str) -> bool:
    """Mark a post as having been notified about.
    
    Args:
        account_did: The DID of the account
        post_id: The ID of the post
        
    Returns:
        bool: True if post was marked as notified, False if already notified
    """
    try:
        # Check if already notified
        existing = NotifiedPost.query.filter_by(
            account_did=account_did,
            post_id=post_id
        ).first()
        
        if existing:
            return False

        # Add notification record
        notification = NotifiedPost(
            account_did=account_did,
            post_id=post_id
        )
        db.session.add(notification)
        db.session.commit()
        
        return True

    except Exception as e:
        db.session.rollback()
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
