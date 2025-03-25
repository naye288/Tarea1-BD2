import pytest
from app.app import create_app, db  # Importa desde app.py
from app.models.reservation import Reservation
from app.models.restaurant import Restaurant
from app.models.user import User
from flask_jwt_extended import create_access_token
from datetime import datetime
from config import TestConfig


@pytest.fixture
def client():
    app = create_app(config_class=TestConfig)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_token(client):
    # Crear un usuario de prueba
    user = User(username='user1', email='user1@example.com', role='user')
    db.session.add(user)
    db.session.commit()

    # Crear un token JWT para el usuario
    access_token = create_access_token(identity=user.id)
    return access_token

@pytest.fixture
def restaurant(client, auth_token):
    # Crear un restaurante de prueba
    restaurant = Restaurant(name="Test Restaurant", admin_id=1)
    db.session.add(restaurant)
    db.session.commit()
    return restaurant

@pytest.fixture
def reservation(client, restaurant, auth_token):
    # Crear una reserva de prueba
    reservation_data = {
        'date': '2025-03-25',
        'time': '18:00',
        'guests': 4,
        'restaurant_id': restaurant.id
    }
    response = client.post('/reservations', json=reservation_data, headers={'Authorization': f'Bearer {auth_token}'})
    return response.get_json()

def test_create_reservation(client, auth_token, restaurant):
    data = {
        'date': '2025-03-25',
        'time': '18:00',
        'guests': 4,
        'restaurant_id': restaurant.id
    }
    response = client.post('/reservations', json=data, headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 201
    assert 'Reservation created successfully' in response.get_json()['message']

def test_create_reservation_missing_fields(client, auth_token, restaurant):
    data = {
        'date': '2025-03-25',
        'guests': 4,
        'restaurant_id': restaurant.id
        # Missing 'time' field
    }
    response = client.post('/reservations', json=data, headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 400
    assert 'Missing required field: time' in response.get_json()['message']

def test_get_reservation(client, reservation):
    reservation_id = reservation['id']
    response = client.get(f'/reservations/{reservation_id}', headers={'Authorization': f'Bearer {reservation["user_id"]}'})
    assert response.status_code == 200
    assert response.get_json()['id'] == reservation_id

def test_get_reservation_not_found(client):
    response = client.get('/reservations/9999', headers={'Authorization': 'Bearer some_token'})
    assert response.status_code == 404
    assert 'Reservation not found' in response.get_json()['message']

def test_cancel_reservation(client, reservation, auth_token):
    reservation_id = reservation['id']
    response = client.delete(f'/reservations/{reservation_id}', headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 200
    assert 'Reservation cancelled successfully' in response.get_json()['message']

def test_cancel_reservation_permission_denied(client, reservation):
    # Try to cancel a reservation with a user that doesn't have permission
    reservation_id = reservation['id']
    user2 = User(username='user2', email='user2@example.com', role='user')
    db.session.add(user2)
    db.session.commit()

    new_token = create_access_token(identity=user2.id)
    response = client.delete(f'/reservations/{reservation_id}', headers={'Authorization': f'Bearer {new_token}'})
    assert response.status_code == 403
    assert 'Permission denied' in response.get_json()['message']

def test_get_user_reservations(client, reservation, auth_token):
    response = client.get('/reservations/user', headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 200
    assert len(response.get_json()) > 0  # There should be at least one reservation

def test_get_restaurant_reservations(client, reservation, restaurant, auth_token):
    response = client.get(f'/reservations/restaurant/{restaurant.id}', headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 200
    assert len(response.get_json()) > 0  # There should be at least one reservation for this restaurant

def test_get_restaurant_reservations_permission_denied(client, reservation, restaurant, auth_token):
    # Use a user that isn't the restaurant admin to test permission denial
    user = User(username='user2', email='user2@example.com', role='user')
    db.session.add(user)
    db.session.commit()

    new_token = create_access_token(identity=user.id)
    response = client.get(f'/reservations/restaurant/{restaurant.id}', headers={'Authorization': f'Bearer {new_token}'})
    assert response.status_code == 403
    assert 'Permission denied' in response.get_json()['message']

def test_create_reservation_invalid_date_format(client, auth_token, restaurant):
    data = {
        'date': 'invalid-date',
        'time': '18:00',
        'guests': 4,
        'restaurant_id': restaurant.id
    }
    response = client.post('/reservations', json=data, headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 400
    assert 'Invalid date format' in response.get_json()['message']

def test_create_reservation_invalid_time_format(client, auth_token, restaurant):
    data = {
        'date': '2025-03-25',
        'time': 'invalid-time',
        'guests': 4,
        'restaurant_id': restaurant.id
    }
    response = client.post('/reservations', json=data, headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 400
    assert 'Invalid time format' in response.get_json()['message']
