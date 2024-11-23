"""
BlueSky Notification API Routes
"""

from flask import Flask, Blueprint, jsonify, request, render_template
from flask_cors import CORS
from ..core.notifier import BlueSkyNotifier
from ..core.database import db, init_db
from ..core.logger import get_logger
import asyncio
import threading
import os
from datetime import datetime

# Get logger for API
logger = get_logger('api')

# Initialize Flask app
app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

# Configure Flask app
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
os.makedirs(DB_PATH, exist_ok=True)
DB_FILE = os.path.join(DB_PATH, 'bluesky_notify.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_FILE}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

logger.info(f"Using database at: {DB_FILE}")

# Initialize database
db.init_app(app)
with app.app_context():
    if not os.path.exists(DB_FILE):
        logger.info("Creating new database")
        init_db(app)
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
bp = Blueprint('api', __name__)

@bp.route('/accounts', methods=['GET'])
def list_accounts():
    """List all monitored accounts."""
    try:
        with app.app_context():
            accounts = notifier.list_accounts()
            return jsonify({"data": {"accounts": accounts}}), 200
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
    """Remove a monitored account."""
    try:
        with app.app_context():
            result = notifier.remove_account(handle)
            if "error" in result:
                return jsonify({"error": result["error"]}), 404
            return jsonify({"data": result})

    except Exception as e:
        logger.error(f"Error removing account: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/accounts/<handle>/preferences', methods=['PUT'])
def update_preferences(handle):
    """Update notification preferences for an account."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Notification preferences required"}), 400

        with app.app_context():
            result = notifier.update_preferences(handle, data)
            if "error" in result:
                return jsonify({"error": result["error"]}), 404
            return jsonify({"data": result})

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

@app.route('/health')
def health_check():
    """Health check endpoint for Docker container."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200

# Register blueprints
app.register_blueprint(bp, url_prefix='/api')

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(host='0.0.0.0', port=3001)
