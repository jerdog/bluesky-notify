"""
Entry point for the Bluesky Notification Tracker application.
"""
from bluesky_notify.api.routes import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001, debug=True)
