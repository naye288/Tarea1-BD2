import pytest
from unittest.mock import patch, MagicMock
from flask import json
from app.app import create_app  # Importa desde app.py
from app.models.user import User
from config import TestConfig


@pytest.fixture
def client():
    app = create_app(config_class=TestConfig)
    with app.test_client() as client:
        yield client

# Helper para simular el token JWT
def mock_jwt_identity(user_id):
    return patch('flask_jwt_extended.get_jwt_identity', return_value=user_id)

# ============================
# GET /users/me
# ============================
@patch('app.models.user.User.query')
def test_get_user_success(mock_query, client):
    user_id = 1
    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_user.username = 'testuser'
    mock_user.email = 'test@example.com'
    mock_user.role = 'client'
    mock_user.created_at = '2024-01-01'

    mock_query.get.return_value = mock_user

    with mock_jwt_identity(user_id):
        response = client.get('/users/me', headers={'Authorization': 'Bearer testtoken'})

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['username'] == 'testuser'
    assert data['email'] == 'test@example.com'

@patch('app.models.user.User.query')
def test_get_user_not_found(mock_query, client):
    user_id = 1
    mock_query.get.return_value = None

    with mock_jwt_identity(user_id):
        response = client.get('/users/me', headers={'Authorization': 'Bearer testtoken'})

    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['message'] == 'User not found'

# ============================
# PUT /users/:id
# ============================
@patch('app.models.user.User.query')
@patch('app.models.user.User.find_by_email')
@patch('app.models.user.User.find_by_username')
def test_update_user_success(mock_find_username, mock_find_email, mock_query, client):
    user_id = 1
    mock_user = MagicMock(spec=User)
    mock_current_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_current_user.id = user_id
    mock_current_user.role = 'client'

    mock_query.get.side_effect = [mock_user, mock_current_user]
    mock_find_email.return_value = None
    mock_find_username.return_value = None

    payload = {
        'email': 'newemail@example.com',
        'username': 'newusername'
    }

    with mock_jwt_identity(user_id):
        response = client.put(f'/users/{user_id}', json=payload, headers={'Authorization': 'Bearer testtoken'})

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == 'User updated successfully'

@patch('app.models.user.User.query')
def test_update_user_not_found(mock_query, client):
    user_id = 1
    mock_query.get.return_value = None

    with mock_jwt_identity(user_id):
        response = client.put(f'/users/{user_id}', json={}, headers={'Authorization': 'Bearer testtoken'})

    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['message'] == 'User not found'

@patch('app.models.user.User.query')
def test_update_user_permission_denied(mock_query, client):
    user_id = 1
    another_user_id = 2
    mock_user = MagicMock(spec=User)
    mock_user.id = another_user_id
    mock_current_user = MagicMock(spec=User)
    mock_current_user.id = user_id
    mock_current_user.role = 'client'

    mock_query.get.side_effect = [mock_user, mock_current_user]

    with mock_jwt_identity(user_id):
        response = client.put(f'/users/{another_user_id}', json={}, headers={'Authorization': 'Bearer testtoken'})

    assert response.status_code == 403
    data = json.loads(response.data)
    assert data['message'] == 'Permission denied'

# ============================
# DELETE /users/:id
# ============================
@patch('app.models.user.User.query')
def test_delete_user_success(mock_query, client):
    user_id = 1
    mock_user = MagicMock(spec=User)
    mock_current_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_current_user.id = user_id
    mock_current_user.role = 'client'

    mock_query.get.side_effect = [mock_user, mock_current_user]

    with mock_jwt_identity(user_id):
        response = client.delete(f'/users/{user_id}', headers={'Authorization': 'Bearer testtoken'})

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == 'User deleted successfully'

@patch('app.models.user.User.query')
def test_delete_user_permission_denied(mock_query, client):
    user_id = 1
    another_user_id = 2
    mock_user = MagicMock(spec=User)
    mock_current_user = MagicMock(spec=User)
    mock_user.id = another_user_id
    mock_current_user.id = user_id
    mock_current_user.role = 'client'

    mock_query.get.side_effect = [mock_user, mock_current_user]

    with mock_jwt_identity(user_id):
        response = client.delete(f'/users/{another_user_id}', headers={'Authorization': 'Bearer testtoken'})

    assert response.status_code == 403
    data = json.loads(response.data)
    assert data['message'] == 'Permission denied'

@patch('app.models.user.User.query')
def test_delete_user_not_found(mock_query, client):
    user_id = 1
    mock_query.get.return_value = None

    with mock_jwt_identity(user_id):
        response = client.delete(f'/users/{user_id}', headers={'Authorization': 'Bearer testtoken'})

    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['message'] == 'User not found'
