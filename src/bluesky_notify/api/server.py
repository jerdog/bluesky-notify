from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from bluesky_notify.core.notifier import BlueSkyNotifier
from bluesky_notify.core.database import (
    db, add_monitored_account, list_monitored_accounts,
    toggle_account_status, update_notification_preferences,
    remove_monitored_account
)
from bluesky_notify.core.config import Config, get_data_dir
from bluesky_notify.core.logger import get_logger
import os
import sys

app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')
CORS(app)

# Load config and set database URI
config = Config()
data_dir = get_data_dir()
db_path = os.path.join(data_dir, 'bluesky_notify.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)
with app.app_context():
    db.create_all()

# Configure Flask logging
import logging
import sys
from werkzeug.serving import WSGIRequestHandler
from bluesky_notify.core.logger import get_logger

# Get our custom logger
logger = get_logger('bluesky_notify')

# Disable default Werkzeug logging and configure Flask
WSGIRequestHandler.log = lambda self, type, message, *args: None
app.logger.handlers = []  # Remove default handlers
app.logger.parent = logger  # Use our logger as parent
app.logger.propagate = True

# Disable Flask's default startup messages
cli = sys.modules.get('flask.cli')
if cli is not None:
    cli.show_server_banner = lambda *args, **kwargs: None

# Disable Werkzeug's development server warning
import werkzeug.serving
werkzeug.serving.is_running_from_reloader = lambda: True

# Global server instance
server = None

@app.route('/')
def index():
    """Render the main dashboard."""
    return render_template('index.html')

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    """List all monitored accounts."""
    accounts = list_monitored_accounts()
    return jsonify(accounts=[{
        'handle': account.handle,
        'display_name': account.display_name,
        'is_active': account.is_active,
        'notification_preferences': {
            pref.type: pref.enabled 
            for pref in account.notification_preferences
        }
    } for account in accounts])

@app.route('/api/accounts', methods=['POST'])
def add_account():
    """Add a new account to monitor."""
    data = request.get_json()
    handle = data.get('handle')
    desktop = data.get('desktop', True)
    email = data.get('email', False)
    
    notifier = BlueSkyNotifier(app=app)
    if not notifier.authenticate():
        return jsonify({'error': 'Failed to authenticate with Bluesky'}), 401
    
    try:
        account_info = notifier.get_account_info(handle)
        notification_preferences = {'desktop': desktop, 'email': email}
        result = add_monitored_account(
            profile_data=account_info,
            notification_preferences=notification_preferences
        )
        
        if 'error' in result:
            return jsonify(result), 400
        return jsonify({'message': f'Successfully added {account_info["display_name"] or handle}'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/accounts/<handle>', methods=['DELETE'])
def remove_account(handle):
    """Remove an account from monitoring."""
    if remove_monitored_account(handle):
        return '', 204
    return jsonify({'error': f'Failed to remove {handle}'}), 400

@app.route('/api/accounts/<handle>/toggle', methods=['POST'])
def toggle_account(handle):
    """Toggle monitoring status for an account."""
    if toggle_account_status(handle):
        return jsonify({'message': f'Successfully toggled status for {handle}'})
    return jsonify({'error': f'Failed to toggle status for {handle}'}), 400

@app.route('/api/accounts/<handle>/preferences', methods=['PATCH'])
def update_preferences(handle):
    """Update notification preferences for an account."""
    data = request.get_json()
    prefs = {}
    if 'desktop' in data:
        prefs['desktop'] = data['desktop']
    if 'email' in data:
        prefs['email'] = data['email']
        
    if update_notification_preferences(handle, prefs):
        return jsonify({'message': f'Successfully updated preferences for {handle}'})
    return jsonify({'error': f'Failed to update preferences for {handle}'}), 400

@app.route('/shutdown', methods=['GET'])
def shutdown():
    """Shutdown the web server."""
    try:
        shutdown_server()
        return 'Server shutting down...'
    except Exception as e:
        return f'Error shutting down: {e}', 500

def shutdown_server():
    """Shutdown the Flask server."""
    global server
    try:
        if server:
            # First try to stop accepting new connections
            server.shutdown()
            # Then close all existing connections
            server.server_close()
            server = None
            logger.info("Web server stopped")
            # Give it a moment to fully close
            import time
            time.sleep(1)
    except Exception as e:
        logger.error(f"Error shutting down web server: {e}")

def run_server(host='127.0.0.1', port=3000, debug=False):
    """Run the Flask web server."""
    global server
    try:
        # Clear any existing Werkzeug server state
        for env_var in ['WERKZEUG_SERVER_FD', 'WERKZEUG_RUN_MAIN']:
            if env_var in os.environ:
                del os.environ[env_var]
        
        # Make sure no existing server is running
        if server:
            shutdown_server()
        
        # Use werkzeug's development server directly
        from werkzeug.serving import make_server
        server = make_server(host, port, app, threaded=True)
        logger.info(f"Starting web server on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Error starting web server: {e}")
        raise  # Re-raise to let the parent thread handle it
