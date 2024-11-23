"""
Database migration script for BlueSky Notify.
This script migrates data from old database locations to the new one.
"""

import os
import sqlite3
from datetime import datetime
import shutil
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.bluesky_notify.core.database import db, init_db
from src.bluesky_notify.api.routes import app

def backup_database(src_path, backup_dir):
    """Create a backup of the database file."""
    if not os.path.exists(src_path):
        return None
    
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'bluesky_notify_{timestamp}.db')
    shutil.copy2(src_path, backup_path)
    return backup_path

def migrate_data(src_path, dest_path):
    """Migrate data from source database to destination database."""
    if not os.path.exists(src_path):
        print(f"Source database not found: {src_path}")
        return False

    try:
        # Connect to source database
        src_conn = sqlite3.connect(src_path)
        src_cur = src_conn.cursor()

        # Connect to destination database
        dest_conn = sqlite3.connect(dest_path)
        dest_cur = dest_conn.cursor()

        # Get all tables from source database
        src_cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = src_cur.fetchall()

        for table in tables:
            table_name = table[0]
            if table_name == 'sqlite_sequence':
                continue

            print(f"Migrating table: {table_name}")

            # Get table data
            src_cur.execute(f"SELECT * FROM {table_name}")
            rows = src_cur.fetchall()

            if not rows:
                print(f"No data in table: {table_name}")
                continue

            # Get column names
            src_cur.execute(f"PRAGMA table_info({table_name})")
            columns = src_cur.fetchall()
            column_names = [col[1] for col in columns]

            # Prepare insert statement
            placeholders = ','.join(['?' for _ in column_names])
            insert_sql = f"INSERT OR IGNORE INTO {table_name} ({','.join(column_names)}) VALUES ({placeholders})"

            # Insert data
            for row in rows:
                try:
                    dest_cur.execute(insert_sql, row)
                except sqlite3.IntegrityError as e:
                    print(f"Skipping duplicate record in {table_name}: {e}")
                except Exception as e:
                    print(f"Error inserting row in {table_name}: {e}")
                    continue

        # Commit changes
        dest_conn.commit()

        # Close connections
        src_conn.close()
        dest_conn.close()

        return True

    except Exception as e:
        print(f"Error migrating database: {e}")
        return False

def main():
    # Define paths
    project_root = os.path.dirname(os.path.abspath(__file__))
    old_paths = [
        os.path.join(project_root, 'bluesky_notify.db'),
        os.path.join(project_root, 'src', 'instance', 'bluesky_notify.db'),
        os.path.join(project_root, 'src', 'data', 'bluesky_notify.db')
    ]
    
    # New database location
    data_dir = os.path.join(project_root, 'data')
    new_db_path = os.path.join(data_dir, 'bluesky_notify.db')
    os.makedirs(data_dir, exist_ok=True)

    # Initialize the new database
    print("Initializing new database...")
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{new_db_path}'
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")

    # Create backups directory
    backup_dir = os.path.join(project_root, 'data', 'backups')
    
    # Process each old database
    for old_path in old_paths:
        if os.path.exists(old_path) and old_path != new_db_path:
            print(f"\nProcessing database: {old_path}")
            
            # Create backup
            backup_path = backup_database(old_path, backup_dir)
            if backup_path:
                print(f"Created backup at: {backup_path}")
            
            # Migrate data
            if migrate_data(old_path, new_db_path):
                print(f"Successfully migrated data from: {old_path}")
                try:
                    # Rename old database to .old
                    old_backup = old_path + '.old'
                    os.rename(old_path, old_backup)
                    print(f"Renamed old database to: {old_backup}")
                except Exception as e:
                    print(f"Error renaming old database: {e}")
            else:
                print(f"Failed to migrate data from: {old_path}")

if __name__ == '__main__':
    main()
