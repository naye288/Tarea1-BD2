import json
import pytest
from datetime import datetime
from flask_jwt_extended import create_access_token
from app.app import create_app
from app.extensions import db
from app.models.restaurant import Restaurant
from app.models.user import User
from config import TestConfig

# ------------------------------
# Fixtures
# ------------------------------

@pytest.fixture
def app():
    app = create_app(config_class=TestConfig)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def init_db(app):
    with app.app_context():
        admin = User(
            username="admin",
            email="admin@example.com",
            password="password",
            role="admin"
        )
        admin.save_to_db()

        restaurant = Restaurant(
            name="Test Restaurant",
            address="123 Test St",
            phone="1234567890",
            open_time=datetime.strptime("09:00", '%H:%M').time(),
            close_time=datetime.strptime("22:00", '%H:%M').time(),
            admin_id=admin.id
        )
        restaurant.save_to_db()

@pytest.fixture
def auth_header(app):
    with app.app_context():
        user = User.query.filter_by(role="admin").first()
        access_token = create_access_token(identity=user.id)
        return {'Authorization': f'Bearer {access_token}'}


# ------------------------------
# Tests de Restaurants
# ------------------------------

def test_create_restaurant_success(client, init_db, auth_header):
    admin = User.query.filter_by(role="admin").first()
    data = {
        "name": "New Restaurant",
        "address": "456 New St",
        "phone": "0987654321",
        "open_time": "10:00",
        "close_time": "22:00" 
    }
    response = client.post('/restaurants', json=data, headers=auth_header)
    assert response.status_code == 201
    assert 'Restaurant created successfully' in response.json['message']

def test_create_restaurant_missing_fields(client, init_db, auth_header):
    data = {
        "name": "Incomplete Restaurant",
        "address": "789 Incomplete St"
    }
    response = client.post('/restaurants', data=json.dumps(data), content_type='application/json', headers=auth_header)
    assert response.status_code == 422

def test_create_restaurant_invalid_time_format(client, init_db, auth_header):
    admin = User.query.filter_by(role="admin").first()
    data = {
        "name": "Invalid Time Restaurant",
        "address": "100 Invalid St",
        "phone": "1234567890",
        "open_time": "10:60",
        "close_time": "22:00",
        "admin_id": admin.id
    }
    response = client.post('/restaurants', data=json.dumps(data), content_type='application/json', headers=auth_header)
    assert response.status_code == 422

def test_get_restaurants(client, init_db):
    response = client.get('/restaurants')
    assert response.status_code == 200
    assert len(response.json) > 0

def test_get_restaurant(client, init_db):
    restaurant = Restaurant.query.first()
    response = client.get(f'/restaurants/{restaurant.id}')
    assert response.status_code == 200
    assert response.json['name'] == restaurant.name

def test_get_restaurant_not_found(client, init_db):
    response = client.get('/restaurants/99999')
    assert response.status_code == 404

def test_update_restaurant_success(client, init_db, auth_header):
    restaurant = Restaurant.query.first()
    data = {
        "name": "Updated Restaurant",
        "address": "123 Updated St",
        "phone": "1234567890",
        "open_time": "08:00",
        "close_time": "23:00",
        "admin_id": restaurant.admin_id
    }
    response = client.put(f'/restaurants/{restaurant.id}', data=json.dumps(data), content_type='application/json', headers=auth_header)
    assert response.status_code == 200

def test_update_restaurant_invalid_time_format(client, init_db, auth_header):
    restaurant = Restaurant.query.first()
    data = {
        "open_time": "25:00",
        "close_time": "22:00"
    }
    response = client.put(f'/restaurants/{restaurant.id}', data=json.dumps(data), content_type='application/json', headers=auth_header)
    assert response.status_code == 422

def test_delete_restaurant_success(client, init_db, auth_header):
    restaurant = Restaurant.query.first()
    response = client.delete(f'/restaurants/{restaurant.id}', headers=auth_header)
    assert response.status_code == 200

def test_delete_restaurant_permission_denied(client, init_db, app):
    with app.app_context():
        user = User(
            username="user",
            email="user@example.com",
            password="password",
            role="client"
        )
        user.save_to_db()
        restaurant = Restaurant.query.first()

        access_token = create_access_token(identity=user.id)
        auth_header = {'Authorization': f'Bearer {access_token}'}

    response = client.delete(f'/restaurants/{restaurant.id}', headers=auth_header)
    assert response.status_code == 403
