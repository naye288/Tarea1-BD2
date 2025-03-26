import pytest
from app.app import create_app, db
from app.models.order import Order, OrderItem
from app.models.restaurant import Restaurant
from app.models.menu import Menu
from app.models.user import User
from flask_jwt_extended import create_access_token
from datetime import datetime
from config import TestConfig


@pytest.fixture
def app():
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
def menu(client, restaurant):
    # Crear un menú de prueba
    menu = Menu(name="Test Dish", price=10.0, category="Main", restaurant_id=restaurant.id)
    db.session.add(menu)
    db.session.commit()
    return menu

@pytest.fixture
def order(client, restaurant, menu, auth_token):
    # Crear una orden de prueba
    order_data = {
        'pickup_time': '2025-03-25 18:00',
        'restaurant_id': restaurant.id,
        'items': [
            {'menu_id': menu.id, 'quantity': 2}
        ]
    }
    response = client.post('/orders', json=order_data, headers={'Authorization': f'Bearer {auth_token}'})
    return response.get_json()

def test_create_order(client, auth_token, restaurant, menu):
    data = {
        'pickup_time': '2025-03-25 18:00',
        'restaurant_id': restaurant.id,
        'items': [
            {'menu_id': menu.id, 'quantity': 2}
        ]
    }
    response = client.post('/orders', json=data, headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 201
    assert 'Order created successfully' in response.get_json()['message']
    assert response.get_json()['total'] == 20.0

def test_create_order_missing_fields(client, auth_token, restaurant):
    data = {
        'pickup_time': '2025-03-25 18:00',
        'restaurant_id': restaurant.id
        # Missing 'items' field
    }
    response = client.post('/orders', json=data, headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 400
    assert 'Missing required field: items' in response.get_json()['message']

def test_get_order(client, order):
    order_id = order['id']
    response = client.get(f'/orders/{order_id}', headers={'Authorization': f'Bearer {order["user_id"]}'})
    assert response.status_code == 200
    assert response.get_json()['id'] == order_id

def test_get_order_not_found(client):
    response = client.get('/orders/9999', headers={'Authorization': 'Bearer some_token'})
    assert response.status_code == 404
    assert 'Order not found' in response.get_json()['message']

def test_update_order_status(client, order, restaurant, auth_token):
    order_id = order['id']
    data = {'status': 'confirmed'}
    response = client.put(f'/orders/{order_id}/status', json=data, headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 200
    assert 'Order status updated successfully' in response.get_json()['message']

def test_update_order_status_permission_denied(client, order, auth_token):
    # Try to update with a user who doesn't have permission
    order_id = order['id']
    data = {'status': 'confirmed'}
    response = client.put(f'/orders/{order_id}/status', json=data, headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 403
    assert 'Permission denied' in response.get_json()['message']

def test_get_user_orders(client, order, auth_token):
    response = client.get('/orders/user', headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 200
    assert len(response.get_json()) > 0  # There should be at least one order

def test_get_restaurant_orders(client, order, restaurant, auth_token):
    response = client.get(f'/orders/restaurant/{restaurant.id}', headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 200
    assert len(response.get_json()) > 0  # There should be at least one order for this restaurant

def test_get_restaurant_orders_permission_denied(client, order, restaurant, auth_token):
    # Use a user that isn't the restaurant admin to test permission denial
    user = User(username='user2', email='user2@example.com', role='user')
    db.session.add(user)
    db.session.commit()

    new_token = create_access_token(identity=user.id)
    response = client.get(f'/orders/restaurant/{restaurant.id}', headers={'Authorization': f'Bearer {new_token}'})
    assert response.status_code == 403
    assert 'Permission denied' in response.get_json()['message']

def test_create_order_invalid_pickup_time(client, auth_token, restaurant, menu):
    data = {
        'pickup_time': 'invalid-time',
        'restaurant_id': restaurant.id,
        'items': [
            {'menu_id': menu.id, 'quantity': 2}
        ]
    }
    response = client.post('/orders', json=data, headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 400
    assert 'Invalid pickup_time format' in response.get_json()['message']

def test_create_order_menu_item_not_found(client, auth_token, restaurant):
    data = {
        'pickup_time': '2025-03-25 18:00',
        'restaurant_id': restaurant.id,
        'items': [
            {'menu_id': 9999, 'quantity': 2}  # Invalid menu ID
        ]
    }
    response = client.post('/orders', json=data, headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 404
    assert 'Menu item 9999 not found' in response.get_json()['message']
