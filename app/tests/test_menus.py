import pytest
from app.app import create_app, db
from app.models.menu import Menu
from app.models.restaurant import Restaurant
from app.models.user import User
from flask_jwt_extended import create_access_token
from config import TestConfig


@pytest.fixture
def client():
    app = create_app(config_class=TestConfig)
    with app.test_client() as client:
        yield client

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_token(client):
    # Crear un usuario de prueba
    user = User(username='admin', email='admin@example.com', role='admin')
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
    menu = Menu(name="Test Menu", price=10.0, category="Main", restaurant_id=restaurant.id)
    db.session.add(menu)
    db.session.commit()
    return menu

def test_create_menu(client, auth_token, restaurant):
    data = {
        'name': 'Test Dish',
        'price': 12.0,
        'category': 'Main',
        'restaurant_id': restaurant.id
    }
    response = client.post('/menus', json=data, headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 201
    assert 'Menu item created successfully' in response.get_json()['message']

def test_get_menu(client, menu):
    response = client.get(f'/menus/{menu.id}')
    assert response.status_code == 200
    assert 'Test Menu' in response.get_json()['name']

def test_get_menu_not_found(client):
    response = client.get('/menus/999')
    assert response.status_code == 404
    assert 'Menu item not found' in response.get_json()['message']

def test_update_menu(client, auth_token, menu):
    data = {
        'name': 'Updated Dish',
        'price': 15.0,
        'category': 'Dessert'
    }
    response = client.put(f'/menus/{menu.id}', json=data, headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 200
    assert 'Menu item updated successfully' in response.get_json()['message']

def test_update_menu_permission_denied(client, menu):
    # Prueba con un token de usuario que no tiene permisos
    data = {
        'name': 'Updated Dish',
        'price': 15.0,
        'category': 'Dessert'
    }
    response = client.put(f'/menus/{menu.id}', json=data)
    assert response.status_code == 403
    assert 'Permission denied' in response.get_json()['message']

def test_delete_menu(client, auth_token, menu):
    response = client.delete(f'/menus/{menu.id}', headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 200
    assert 'Menu item deleted successfully' in response.get_json()['message']

def test_delete_menu_not_found(client):
    response = client.delete('/menus/999')
    assert response.status_code == 404
    assert 'Menu item not found' in response.get_json()['message']

def test_get_restaurant_menus(client, restaurant):
    menu1 = Menu(name="Dish 1", price=10.0, category="Main", restaurant_id=restaurant.id)
    menu2 = Menu(name="Dish 2", price=8.0, category="Appetizer", restaurant_id=restaurant.id)
    db.session.add(menu1)
    db.session.add(menu2)
    db.session.commit()

    response = client.get(f'/menus/restaurant/{restaurant.id}')
    assert response.status_code == 200
    assert len(response.get_json()) == 2
    assert 'Dish 1' in response.get_json()[0]['name']
    assert 'Dish 2' in response.get_json()[1]['name']

def test_create_menu_missing_fields(client, auth_token, restaurant):
    # Prueba de error cuando falta un campo
    data = {
        'name': 'Incomplete Dish',
        'price': 12.0,
        'category': 'Main'
        # restaurant_id está faltando
    }
    response = client.post('/menus', json=data, headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 400
    assert 'Missing required field' in response.get_json()['message']

def test_create_menu_restaurant_not_found(client, auth_token):
    # Prueba cuando el restaurante no existe
    data = {
        'name': 'Test Dish',
        'price': 12.0,
        'category': 'Main',
        'restaurant_id': 999  # ID de restaurante no válido
    }
    response = client.post('/menus', json=data, headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 404
    assert 'Restaurant not found' in response.get_json()['message']
