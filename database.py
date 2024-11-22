from sqlalchemy import create_engine, Column, Integer, String, Boolean, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import UniqueConstraint
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class MonitoredAccount(Base):
    __tablename__ = 'monitored_accounts'
    
    id = Column(Integer, primary_key=True)
    did = Column(String, unique=True, nullable=False)
    handle = Column(String, nullable=False)
    avatar_url = Column(String)
    display_name = Column(String)
    is_active = Column(Boolean, default=True)
    notification_preferences = Column(JSON, default=lambda: {"desktop": True, "email": False})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NotifiedPost(Base):
    __tablename__ = 'notified_posts'
    
    id = Column(Integer, primary_key=True)
    account_did = Column(String, nullable=False)
    post_id = Column(String, nullable=False)
    notified_at = Column(DateTime, default=datetime.utcnow)
    
    # Ensure we don't notify about the same post twice
    __table_args__ = (
        UniqueConstraint('account_did', 'post_id', name='_account_post_uc'),
    )

class DatabaseManager:
    def __init__(self, db_path='bluesky_notify.db'):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def add_monitored_account(self, did, handle, display_name=None, notification_preferences=None, avatar_url=None):
        """Add a new account to monitor"""
        if notification_preferences is None:
            notification_preferences = {'desktop': True, 'email': False}
            
        session = self.Session()
        try:
            account = MonitoredAccount(
                did=did,
                handle=handle,
                display_name=display_name,
                notification_preferences=notification_preferences,
                avatar_url=avatar_url
            )
            session.add(account)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding account: {e}")
            return False
        finally:
            session.close()
    
    def is_post_notified(self, account_did, post_id):
        """
        Check if a post has already been notified about.
        
        Args:
            account_did (str): The DID of the account
            post_id (str): The ID of the post
            
        Returns:
            bool: True if the post has been notified about, False otherwise
        """
        session = self.Session()
        try:
            existing = session.query(NotifiedPost).filter_by(
                account_did=account_did,
                post_id=post_id
            ).first()
            return existing is not None
        finally:
            session.close()
    
    def mark_post_notified(self, account_did, post_id):
        """
        Mark a post as having been notified about.
        
        Args:
            account_did (str): The DID of the account
            post_id (str): The ID of the post
            
        Returns:
            bool: True if successful, False otherwise
        """
        session = self.Session()
        try:
            post = NotifiedPost(
                account_did=account_did,
                post_id=post_id
            )
            session.add(post)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error marking post as notified: {e}")
            return False
        finally:
            session.close()

    def get_monitored_accounts(self):
        session = self.Session()
        try:
            accounts = session.query(MonitoredAccount).all()
            return [{
                'did': account.did, 
                'handle': account.handle,
                'is_active': account.is_active,
                'notification_preferences': account.notification_preferences,
                'avatar_url': account.avatar_url,
                'display_name': account.display_name
            } for account in accounts]
        finally:
            session.close()
    
    def update_notification_preferences(self, did, preferences):
        """
        Update notification preferences for an account
        
        Args:
            did (str): The DID of the account
            preferences (dict): Dictionary containing notification preferences
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.Session() as session:
                account = session.query(MonitoredAccount).filter_by(did=did).first()
                if account:
                    account.notification_preferences = preferences
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating notification preferences: {e}")
            return False
    
    def toggle_account_active(self, did):
        session = self.Session()
        try:
            account = session.query(MonitoredAccount).filter_by(did=did).first()
            if account:
                account.is_active = not account.is_active
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error toggling account status: {e}")
            return False
        finally:
            session.close()
    
    def remove_monitored_account(self, did):
        session = self.Session()
        try:
            account = session.query(MonitoredAccount).filter_by(did=did).first()
            if account:
                session.delete(account)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error removing monitored account: {e}")
            return False
        finally:
            session.close()
