"""
BlueSky Notification Web Interface

This module provides a web interface for managing BlueSky notifications.
It allows users to add/remove monitored accounts and view their status.
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_migrate import Migrate
from notifier import BlueSkyNotifier
from database import Base
import logging
import threading
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    filename='bluesky_notify.log'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bluesky_notify.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize migrations
migrate = Migrate(app, Base)

# Initialize the notifier
notifier = BlueSkyNotifier()

# Start the notifier in a background thread
def run_notifier():
    """Run the notifier in the background"""
    if notifier.authenticate():
        notifier.run()
    else:
        logger.error("Failed to start notifier: Authentication failed")

notifier_thread = threading.Thread(target=run_notifier, daemon=True)
notifier_thread.start()

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/accounts', methods=['GET'])
def list_accounts():
    """List all monitored accounts"""
    try:
        accounts = notifier.db_manager.get_monitored_accounts()
        return jsonify({"success": True, "accounts": accounts})
    except Exception as e:
        logger.error(f"Error listing accounts: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/accounts', methods=['POST'])
def add_account():
    """Add a new account to monitor"""
    try:
        if not getattr(notifier, '_authenticated', False) and not notifier.authenticate():
            return jsonify({
                "success": False, 
                "error": "Not authenticated with BlueSky"
            }), 401

        data = request.get_json()
        handle = data.get('handle', '').strip()
        
        if not handle:
            return jsonify({"success": False, "error": "Handle is required"}), 400
            
        # Get account info from BlueSky
        account_info = notifier.get_account_info(handle)
        
        # Add account to database
        success = notifier.db_manager.add_monitored_account(
            did=account_info['did'],
            handle=account_info['handle'],
            display_name=account_info['display_name'],
            avatar_url=account_info['avatar_url']
        )
        
        if success:
            return jsonify({"success": True, "message": f"Added {handle} to monitored accounts"})
        else:
            return jsonify({"success": False, "error": "Account already being monitored"}), 400
            
    except Exception as e:
        logger.error(f"Error adding account: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/accounts/<handle>', methods=['DELETE'])
def remove_account(handle):
    """Remove a monitored account"""
    try:
        if not getattr(notifier, '_authenticated', False) and not notifier.authenticate():
            return jsonify({
                "success": False, 
                "error": "Not authenticated with BlueSky"
            }), 401

        # Remove @ symbol if present
        if handle.startswith('@'):
            handle = handle[1:]
            
        # Get the account's DID first
        profile = notifier.client.get_profile(handle)
        if notifier.db_manager.remove_monitored_account(profile.did):
            return jsonify({"success": True})
        else:
            return jsonify({
                "success": False,
                "error": "Failed to remove account"
            }), 400
            
    except Exception as e:
        logger.error(f"Error removing account: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/accounts/<handle>/toggle', methods=['POST'])
def toggle_account(handle):
    """Toggle account monitoring status"""
    try:
        if not getattr(notifier, '_authenticated', False) and not notifier.authenticate():
            return jsonify({
                "success": False, 
                "error": "Not authenticated with BlueSky"
            }), 401

        # Remove @ symbol if present
        if handle.startswith('@'):
            handle = handle[1:]
        
        # First get the account from our database
        accounts = notifier.db_manager.get_monitored_accounts()
        account = next((acc for acc in accounts if acc['handle'].lower() == handle.lower()), None)
        
        if not account:
            return jsonify({
                "success": False,
                "error": "Account not found"
            }), 404
            
        if notifier.db_manager.toggle_account_active(account['did']):
            return jsonify({"success": True})
        else:
            return jsonify({
                "success": False,
                "error": "Failed to toggle account"
            }), 400
            
    except Exception as e:
        logger.error(f"Error toggling account: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/accounts/<handle>/preferences', methods=['PUT'])
def update_preferences(handle):
    """Update notification preferences for an account"""
    try:
        if not getattr(notifier, '_authenticated', False) and not notifier.authenticate():
            return jsonify({
                "success": False, 
                "error": "Not authenticated with BlueSky"
            }), 401

        data = request.get_json()
        preferences = {
            'desktop': data.get('desktop', True),
            'email': data.get('email', False)
        }
        
        # Remove @ symbol if present
        if handle.startswith('@'):
            handle = handle[1:]
        
        # First get the account from our database
        accounts = notifier.db_manager.get_monitored_accounts()
        account = next((acc for acc in accounts if acc['handle'].lower() == handle.lower()), None)
        
        if not account:
            return jsonify({
                "success": False,
                "error": "Account not found"
            }), 404
            
        if notifier.db_manager.update_notification_preferences(account['did'], preferences):
            return jsonify({"success": True})
        else:
            return jsonify({
                "success": False,
                "error": "Failed to update preferences"
            }), 400
            
    except Exception as e:
        logger.error(f"Error updating preferences for {handle}: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get the notifier status"""
    return jsonify({
        "success": True,
        "authenticated": getattr(notifier, '_authenticated', False),
        "running": notifier_thread.is_alive()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001)
