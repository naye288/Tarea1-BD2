import json
import pytest
from unittest.mock import patch, MagicMock
from app import create_app  # Asegúrate de tener una función para crear tu app Flask
from app.models.user import User


@pytest.fixture
def client():
    app = create_app(testing=True)
    with app.test_client() as client:
        yield client


def test_register_success(client):
    # Datos de prueba para registro exitoso
    user_data = {
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'testpassword',
        'role': 'client'
    }

    with patch.object(User, 'find_by_username', return_value=None), \
         patch.object(User, 'find_by_email', return_value=None), \
         patch.object(User, 'generate_hash', return_value='hashed_password'), \
         patch.object(User, 'save_to_db', return_value=True):

        response = client.post('/register', data=json.dumps(user_data), content_type='application/json')

        assert response.status_code == 201
        assert response.json['message'] == 'User created successfully'


def test_register_existing_username(client):
    user_data = {
        'username': 'existinguser',
        'email': 'newemail@example.com',
        'password': 'password'
    }

    with patch.object(User, 'find_by_username', return_value=MagicMock()):
        response = client.post('/register', data=json.dumps(user_data), content_type='application/json')

        assert response.status_code == 400
        assert response.json['message'] == 'Username already exists'


def test_register_existing_email(client):
    user_data = {
        'username': 'newuser',
        'email': 'existingemail@example.com',
        'password': 'password'
    }

    with patch.object(User, 'find_by_username', return_value=None), \
         patch.object(User, 'find_by_email', return_value=MagicMock()):

        response = client.post('/register', data=json.dumps(user_data), content_type='application/json')

        assert response.status_code == 400
        assert response.json['message'] == 'Email already exists'


def test_register_invalid_role(client):
    user_data = {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'password',
        'role': 'invalidrole'
    }

    with patch.object(User, 'find_by_username', return_value=None), \
         patch.object(User, 'find_by_email', return_value=None):

        response = client.post('/register', data=json.dumps(user_data), content_type='application/json')

        assert response.status_code == 400
        assert response.json['message'] == 'Invalid role'


def test_login_success(client):
    user_data = {
        'username': 'testuser',
        'password': 'testpassword'
    }

    fake_user = MagicMock()
    fake_user.id = 1
    fake_user.role = 'client'
    fake_user.password = 'hashed_password'

    with patch.object(User, 'find_by_username', return_value=fake_user), \
         patch.object(User, 'verify_hash', return_value=True), \
         patch('app.routes.auth.create_access_token', return_value='fake_token'):

        response = client.post('/login', data=json.dumps(user_data), content_type='application/json')

        assert response.status_code == 200
        assert response.json['message'] == 'Logged in successfully'
        assert response.json['access_token'] == 'fake_token'
        assert response.json['user_id'] == fake_user.id
        assert response.json['role'] == fake_user.role


def test_login_user_not_found(client):
    user_data = {
        'username': 'nonexistentuser',
        'password': 'testpassword'
    }

    with patch.object(User, 'find_by_username', return_value=None):

        response = client.post('/login', data=json.dumps(user_data), content_type='application/json')

        assert response.status_code == 404
        assert response.json['message'] == 'User not found'


def test_login_invalid_password(client):
    user_data = {
        'username': 'testuser',
        'password': 'wrongpassword'
    }

    fake_user = MagicMock()
    fake_user.password = 'hashed_password'

    with patch.object(User, 'find_by_username', return_value=fake_user), \
         patch.object(User, 'verify_hash', return_value=False):

        response = client.post('/login', data=json.dumps(user_data), content_type='application/json')

        assert response.status_code == 401
        assert response.json['message'] == 'Invalid credentials'
