"""
Configuration settings for the Bluesky Notification Tracker.
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# Database
SQLALCHEMY_DATABASE_URI = os.getenv(
    'DATABASE_URL',
    f'sqlite:///{BASE_DIR}/bluesky_notify.db'
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Bluesky API
BLUESKY_USERNAME = os.getenv('BLUESKY_USERNAME')
BLUESKY_PASSWORD = os.getenv('BLUESKY_PASSWORD')

# Logging
LOG_FILE = os.getenv('LOG_FILE', 'bluesky_notify.log')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
