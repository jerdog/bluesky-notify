"""
BlueSky Notification API Routes
"""

from flask import Flask, Blueprint, jsonify, request, render_template
from flask_cors import CORS
from ..core.notifier import BlueSkyNotifier
from ..core.database import db, MonitoredAccount
from ..core.logger import get_logger
from ..core.config import get_data_dir
import asyncio
import threading
import os
from datetime import datetime
import pathlib

# Get logger for API
logger = get_logger('api')

# Create Blueprint first
bp = Blueprint('api', __name__)

# Initialize Flask app
app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

# Configure Flask app
# Use consistent database path from config
DB_PATH = pathlib.Path(get_data_dir())
DB_PATH.mkdir(exist_ok=True)
DB_FILE = DB_PATH / 'bluesky_notify.db'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_FILE}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

logger.info(f"Using database at: {DB_FILE}")

# Initialize database
db.init_app(app)
with app.app_context():
    if not DB_FILE.exists():
        logger.info("Creating new database")
        db.create_all()
    else:
        logger.info("Using existing database")

# Initialize notifier
notifier = BlueSkyNotifier(app)

def run_notifier():
    """Run the notifier in a background thread."""
    try:
        logger.info("Starting notifier background thread")
        with app.app_context():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(notifier.run())
    except Exception as e:
        logger.error(f"Notifier thread error: {str(e)}")

# Start notifier in background thread
notifier_thread = threading.Thread(target=run_notifier, daemon=True)
notifier_thread.start()

# API Routes
@bp.route('/accounts', methods=['GET'])
def list_accounts():
    """List all monitored accounts."""
    try:
        with app.app_context():
            # Ensure we're using a fresh session
            db.session.remove()
            accounts = notifier.list_accounts()
            return jsonify({"data": {"accounts": [account.to_dict() for account in accounts]}}), 200
    except Exception as e:
        logger.error(f"Error listing accounts: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/accounts', methods=['POST'])
def add_account():
    """Add a new account to monitor."""
    try:
        data = request.get_json()
        if not data or 'handle' not in data:
            return jsonify({"error": "Handle is required"}), 400

        handle = data['handle']
        preferences = data.get('notification_preferences')

        with app.app_context():
            # Run add_account in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(notifier.add_account(handle, preferences))
            loop.close()

            if "error" in result:
                return jsonify({"error": result["error"]}), 400
            return jsonify({"data": result}), 201

    except Exception as e:
        logger.error(f"Error adding account: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/accounts/<handle>', methods=['DELETE'])
def remove_account(handle):
    """Remove a monitored account by handle."""
    try:
        with app.app_context():
            result = notifier.remove_account(handle, by_did=False)
            if "error" in result:
                return jsonify({"error": result["error"]}), 400
            return jsonify({"data": result}), 200
    except Exception as e:
        logger.error(f"Error removing account: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/accounts/did/<did>', methods=['DELETE'])
def remove_account_by_did(did):
    """Remove a monitored account by DID."""
    logger.info(f"Received DELETE request for account with DID: {did}")
    try:
        with app.app_context():
            # Debug: Check if account exists first
            account = MonitoredAccount.query.filter_by(did=did).first()
            if account:
                logger.info(f"Found account in database - DID: {account.did}, Handle: {account.handle}")
            else:
                logger.warning(f"No account found with DID: {did}")
                return jsonify({"error": f"Account with DID {did} not found"}), 404

            # Try to remove the account
            result = notifier.remove_account(did, by_did=True)
            logger.info(f"Account removal result: {result}")

            if "error" in result:
                logger.warning(f"Error removing account: {result['error']}")
                return jsonify({"error": result["error"]}), 400

            logger.info("Account removed successfully")
            return jsonify({"data": result}), 200

    except Exception as e:
        error_msg = f"Error removing account by DID: {str(e)}"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), 500

@bp.route('/accounts/<handle>/preferences', methods=['PUT'])
def update_preferences(handle):
    """Update notification preferences for an account."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Notification preferences required"}), 400

        with app.app_context():
            # Ensure we're using a fresh session
            db.session.remove()
            result = notifier.update_preferences(handle, data)
            if "error" in result:
                return jsonify({"error": result["error"]}), 404
            return jsonify({"data": result}), 200

    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/accounts/<handle>/toggle', methods=['POST'])
def toggle_account(handle):
    """Toggle monitoring status for an account."""
    try:
        with app.app_context():
            result = notifier.toggle_account(handle)
            if "error" in result:
                return jsonify({"error": result["error"]}), 404
            return jsonify({"data": result})

    except Exception as e:
        logger.error(f"Error toggling account: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')

# Register blueprints
app.register_blueprint(bp, url_prefix='/api')

if __name__ == '__main__':
    default_port = 5001
    port = int(os.environ.get('PORT', default_port))
    app.run(host='0.0.0.0', port=port, debug=False)
