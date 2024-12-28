from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import sys
from queue import Queue
from threading import Lock

from bluesky_notify.core.notifier import BlueSkyNotifier
from bluesky_notify.core.database import (
    db, add_monitored_account, list_monitored_accounts,
    toggle_account_status, update_notification_preferences,
    remove_monitored_account
)
from bluesky_notify.core.config import Config, get_data_dir
from bluesky_notify.core.logger import get_logger

# Initialize WebSocket support only in Docker
if os.getenv('DOCKER_CONTAINER'):
    try:
        from flask_sock import Sock
        has_websocket = True
    except ImportError:
        has_websocket = False
else:
    has_websocket = False

app = Flask(__name__,
           template_folder='../templates',
           static_folder='../static')
CORS(app)

# Initialize WebSocket only if available and in Docker
if has_websocket:
    sock = Sock(app)
    ws_clients = set()
    ws_lock = Lock()
    notification_queue = Queue()

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

    notifier = BlueSkyNotifier(app=app)

    try:
        account_info = notifier.get_account_info(handle)
        notification_preferences = {'desktop': desktop}
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

    if update_notification_preferences(handle, prefs):
        return jsonify({'message': f'Successfully updated preferences for {handle}'})
    return jsonify({'error': f'Failed to update preferences for {handle}'}), 400

def broadcast_notification(title, message, url):
    """Broadcast a notification to all connected WebSocket clients."""
    if not has_websocket:
        return


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

        # Use Flask's built-in server with debug output
        logger.info(f"Starting web server on http://{host}:{port}")
        app.logger.setLevel(logging.DEBUG if debug else logging.INFO)

        # Test routes are accessible
        logger.debug("Testing routes...")
        test_routes = [
            ('/', 'index'),
            ('/api/accounts', 'get_accounts'),
            ('/api/accounts', 'add_account'),
        ]
        for route, endpoint in test_routes:
            logger.debug(f"Testing route: {route} -> {endpoint}")
            if endpoint not in app.view_functions:
                logger.error(f"Route {route} -> {endpoint} not found!")

        # Set up routes before running
        logger.debug("Setting up routes...")
        app.add_url_rule('/', 'index', index)
        app.add_url_rule('/api/accounts', 'get_accounts', get_accounts, methods=['GET'])
        app.add_url_rule('/api/accounts', 'add_account', add_account, methods=['POST'])
        app.add_url_rule('/api/accounts/<handle>', 'remove_account', remove_account, methods=['DELETE'])
        app.add_url_rule('/api/accounts/<handle>/toggle', 'toggle_account', toggle_account, methods=['POST'])
        app.add_url_rule('/api/accounts/<handle>/preferences', 'update_preferences', update_preferences, methods=['PATCH'])

        # Run the server
        logger.debug("Starting Flask server...")
        import werkzeug
        werkzeug.serving.is_running_from_reloader = lambda: False

        # Create server instance
        try:
            srv = werkzeug.serving.make_server(
                host=host,
                port=port,
                app=app,
                threaded=True,
                processes=1,
                ssl_context=None
            )
        except Exception as e:
            logger.error(f"Failed to create server: {e}")
            raise

        # Store server instance
        server = srv

        # Start serving
        try:
            srv.serve_forever()
        except Exception as e:
            logger.error(f"Server failed while running: {e}")
            raise

    except Exception as e:
        logger.error(f"Error starting web server: {e}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        raise  # Re-raise to let the parent thread handle it
