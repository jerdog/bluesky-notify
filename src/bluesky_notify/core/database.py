"""
Database models for the BlueSky notification system.
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
    """Account model for storing BlueSky account information."""
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
    """Notification preferences for accounts."""
    __tablename__ = 'notification_preferences'

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('monitored_accounts.id'))
    type = Column(String)  # 'desktop' or 'email'
    enabled = Column(Boolean, default=True)
    account = relationship('MonitoredAccount', back_populates='notification_preferences')

class NotifiedPost(db.Model):
    """Record of posts that have been notified about."""
    __tablename__ = 'notified_posts'

    id = Column(Integer, primary_key=True)
    account_did = Column(String)
    post_id = Column(String)
    notified_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('account_did', 'post_id', name='_account_post_uc'),
    )

def get_monitored_accounts():
    """Get all monitored accounts with their preferences."""
    try:
        accounts = []
        # Eager load notification preferences
        for account in MonitoredAccount.query.options(db.joinedload(MonitoredAccount.notification_preferences)).all():
            accounts.append({
                'did': account.did,
                'handle': account.handle,
                'display_name': account.display_name,
                'avatar_url': account.avatar_url,
                'is_active': account.is_active,
                'notification_preferences': {
                    pref.type: pref.enabled
                    for pref in account.notification_preferences
                }
            })
        return accounts
    except Exception as e:
        logger.error(f"Error getting monitored accounts: {str(e)}")
        return []

def add_monitored_account(account_info, notification_preferences=None):
    """Add a new monitored account."""
    try:
        account = MonitoredAccount.query.filter_by(handle=account_info['handle']).first()
        if account:
            return {"error": "Account already exists"}

        account = MonitoredAccount(
            did=account_info['did'],
            handle=account_info['handle'],
            display_name=account_info.get('display_name'),
            avatar_url=account_info.get('avatar_url'),
            is_active=True
        )
        db.session.add(account)

        if notification_preferences:
            for pref_type, enabled in notification_preferences.items():
                pref = NotificationPreference(
                    account=account,
                    type=pref_type,
                    enabled=enabled
                )
                db.session.add(pref)

        db.session.commit()
        return {
            "message": "Account added successfully",
            "account": {
                "did": account.did,
                "handle": account.handle,
                "display_name": account.display_name,
                "avatar_url": account.avatar_url,
                "is_active": account.is_active,
                "notification_preferences": notification_preferences or {}
            }
        }
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding monitored account: {str(e)}")
        return {"error": str(e)}

def remove_monitored_account(handle):
    """Remove a monitored account."""
    try:
        account = MonitoredAccount.query.filter_by(handle=handle).first()
        if not account:
            return {"error": "Account not found"}

        db.session.delete(account)
        db.session.commit()
        return {"message": "Account removed successfully"}
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing monitored account: {str(e)}")
        return {"error": str(e)}

def mark_post_notified(account_did, post_id):
    """Mark a post as having been notified about."""
    try:
        # Check if post is already marked as notified
        existing = NotifiedPost.query.filter_by(
            account_did=account_did,
            post_id=post_id
        ).first()

        if existing:
            # Update the notification time if it exists
            existing.notified_at = datetime.utcnow()
            db.session.commit()
            return True

        # Create new notification record if it doesn't exist
        notified = NotifiedPost(
            account_did=account_did,
            post_id=post_id,
            notified_at=datetime.utcnow()
        )
        db.session.add(notified)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error marking post as notified: {str(e)}")
        return False

def init_db(app):
    """Initialize the database with the Flask app context."""
    try:
        db.create_all()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
