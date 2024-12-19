import pytest
from unittest.mock import patch, MagicMock
import os
import threading
import time
from bluesky_notify.api.server import run_server, app, shutdown_server

@pytest.fixture
def mock_logger():
    with patch('bluesky_notify.api.server.logger') as mock:
        yield mock

@pytest.fixture
def mock_werkzeug():
    with patch('werkzeug.serving.make_server') as mock:
        yield mock

@pytest.fixture
def mock_server():
    server = MagicMock()
    server.serve_forever = MagicMock()
    server.shutdown = MagicMock()
    server.server_close = MagicMock()
    return server

def test_server_lifecycle(mock_logger, mock_werkzeug, mock_server):
    mock_werkzeug.return_value = mock_server

    # Start server in thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    # Give server time to start
    time.sleep(0.1)

    # Verify server started
    assert mock_werkzeug.called
    assert mock_server.serve_forever.called

    # Shutdown server
    shutdown_server()

    # Verify shutdown sequence
    assert mock_server.shutdown.called
    assert mock_server.server_close.called

    # Allow thread to complete
    server_thread.join(timeout=1)
    assert not server_thread.is_alive()

def test_server_error_handling(mock_logger, mock_werkzeug):
    mock_werkzeug.side_effect = Exception("Server error")

    with pytest.raises(Exception):
        run_server()

    assert mock_logger.error.called