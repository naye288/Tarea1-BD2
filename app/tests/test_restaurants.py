import pytest
from datetime import datetime
from app.app import create_app, db
from app.models.restaurant import Restaurant
from app.models.user import User
from flask_jwt_extended import create_access_token
from config import TestConfig

@pytest.fixture
def cliente():
    app = create_app(config_class=TestConfig)
    with app.test_client() as cliente:
        yield cliente

@pytest.fixture    
def init_db(cliente):
    """Initialize the database for testing."""
    with cliente.app_context():
        db.create_all()  # Ensure the app context is active when using SQLAlchemy
    
        # Crear un usuario admin para pruebas
        admin = User(username="admin", email="admin@example.com", password="password", role="admin")
        db.session.add(admin)
        db.session.commit()
        
        # Crear un restaurante de ejemplo
        restaurant = Restaurant(
            name="Test Restaurant",
            address="123 Test St",
            phone="1234567890",
            open_time=datetime.strptime("09:00", '%H:%M').time(),
            close_time=datetime.strptime("22:00", '%H:%M').time(),
            admin_id=admin.id
        )
        db.session.add(restaurant)
        db.session.commit()
 
@pytest.fixture 
def auth_header(cliente):
    # Obtener el token JWT de un usuario admin
    user = User.query.filter_by(role="admin").first()
    access_token = create_access_token(identity=user.id)
    return {'Authorization': f'Bearer {access_token}'}

def test_create_restaurant(cliente, auth_header):
    data = {
        "name": "New Restaurant",
        "address": "456 New St",
        "phone": "0987654321",
        "open_time": "10:00",
        "close_time": "22:00"
    }
    
    response = cliente.post('/restaurants', json=data, headers=auth_header)
    assert response.status_code == 201
    assert 'Restaurant created successfully' in response.json['message']


def test_create_restaurant_missing_fields(test_client, auth_header):
    data = {
        "name": "Incomplete Restaurant",
        "address": "789 Incomplete St"
    }
    
    response = test_client.post('/restaurants', json=data, headers=auth_header)
    assert response.status_code == 400
    assert 'Missing required field: phone' in response.json['message']

def test_create_restaurant_invalid_time_format(test_client, auth_header):
    data = {
        "name": "Invalid Time Restaurant",
        "address": "100 Invalid St",
        "phone": "1234567890",
        "open_time": "10:60",  # Invalid time format
        "close_time": "22:00"
    }
    
    response = test_client.post('/restaurants', json=data, headers=auth_header)
    assert response.status_code == 400
    assert 'Invalid time format. Use HH:MM' in response.json['message']

def test_get_restaurants(test_client):
    response = test_client.get('/restaurants')
    assert response.status_code == 200
    assert len(response.json) > 0  # Verificar que hay al menos un restaurante

def test_get_restaurant(test_client):
    restaurant = Restaurant.query.first()
    response = test_client.get(f'/restaurants/{restaurant.id}')
    assert response.status_code == 200
    assert response.json['name'] == restaurant.name

def test_get_restaurant_not_found(test_client):
    response = test_client.get('/restaurants/99999')  # ID que no existe
    assert response.status_code == 404
    assert 'Restaurant not found' in response.json['message']

def test_update_restaurant(test_client, auth_header):
    restaurant = Restaurant.query.first()
    data = {
        "name": "Updated Restaurant",
        "address": "123 Updated St",
        "phone": "1234567890",
        "open_time": "08:00",
        "close_time": "23:00"
    }
    
    response = test_client.put(f'/restaurants/{restaurant.id}', json=data, headers=auth_header)
    assert response.status_code == 200
    assert 'Restaurant updated successfully' in response.json['message']

def test_update_restaurant_invalid_time_format(test_client, auth_header):
    restaurant = Restaurant.query.first()
    data = {
        "open_time": "25:00",  # Invalid time format
        "close_time": "22:00"
    }
    
    response = test_client.put(f'/restaurants/{restaurant.id}', json=data, headers=auth_header)
    assert response.status_code == 400
    assert 'Invalid open_time format. Use HH:MM' in response.json['message']

def test_delete_restaurant(test_client, auth_header):
    restaurant = Restaurant.query.first()
    response = test_client.delete(f'/restaurants/{restaurant.id}', headers=auth_header)
    assert response.status_code == 200
    assert 'Restaurant deleted successfully' in response.json['message']

def test_delete_restaurant_permission_denied(test_client, auth_header):
    # Crear un usuario no admin
    user = User(username="user", email="user@example.com", password="password", role="user")
    db.session.add(user)
    db.session.commit()
    
    restaurant = Restaurant.query.first()
    access_token = create_access_token(identity=user.id)
    auth_header = {'Authorization': f'Bearer {access_token}'}
    
    response = test_client.delete(f'/restaurants/{restaurant.id}', headers=auth_header)
    assert response.status_code == 403
    assert 'Permission denied' in response.json['message']