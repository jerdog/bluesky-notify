import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
from bluesky_notify.api.routes import app, bp
from bluesky_notify.core.database import db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

@pytest.fixture
def mock_notifier():
    mock = Mock()
    # Set up synchronous methods
    mock.list_accounts.return_value = [
        Mock(to_dict=lambda: {
            'handle': 'test_user',
            'display_name': 'Test User',
            'is_active': True
        })
    ]
    mock.remove_account.return_value = {'message': 'Account removed'}
    mock.toggle_account.return_value = {'handle': 'test_user', 'is_active': False}
    mock.update_preferences.return_value = {
        'handle': 'test_user',
        'preferences': {'desktop': True}
    }

    # Set up async method
    async_mock = AsyncMock()
    async_mock.return_value = {'handle': 'test_user', 'display_name': 'Test User'}
    mock.add_account = async_mock

    with patch('bluesky_notify.api.routes.BlueSkyNotifier', return_value=mock):
        yield mock

def test_list_accounts(client, mock_notifier):
    response = client.get('/api/accounts')
    assert response.status_code == 200
    assert len(response.json['data']['accounts']) == 1

def test_add_account(client, mock_notifier):
    response = client.post('/api/accounts', json={
        'handle': 'test_user',
        'notification_preferences': {'desktop': True}
    })
    assert response.status_code == 201

def test_remove_account(client, mock_notifier):
    response = client.delete('/api/accounts/test_user')
    assert response.status_code == 200

def test_update_preferences(client, mock_notifier):
    response = client.put('/api/accounts/test_user/preferences',
                         json={'desktop': True})
    assert response.status_code == 200

def test_toggle_account(client, mock_notifier):
    response = client.post('/api/accounts/test_user/toggle')
    assert response.status_code == 200

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_invalid_account_handle(client, mock_notifier):
    mock_notifier.add_account.return_value = {"error": "Invalid handle"}

    response = client.post('/api/accounts', json={
        'handle': 'invalid@handle'
    })
    assert response.status_code == 400
    assert 'error' in response.json