import pytest
from app.app import create_app
from app.extensions import db
from app.models.menu import Menu
from app.models.restaurant import Restaurant
from app.models.user import User
from flask_jwt_extended import create_access_token
from config import TestConfig

# ---------------------- FIXTURE BASE ----------------------

@pytest.fixture(scope="session")
def app():
    app = create_app(config_class=TestConfig)
    app.config['TESTING'] = True

    with app.app_context():
        db.drop_all()
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()

# ---------------------- USERS ----------------------

@pytest.fixture(scope="function")
def admin_user(app):
    with app.app_context():
        user = User(username='admin', email='admin@example.com', password='test', role='admin')
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user

@pytest.fixture(scope="function")
def auth_token(admin_user):
    return create_access_token(identity=admin_user.id)

# ---------------------- RESTAURANTS ----------------------

@pytest.fixture(scope="function")
def restaurant(admin_user):
    with db.session.begin():
        r = Restaurant(name="Test Restaurant", address="Street 123", phone="123456789",
                       open_time="09:00", close_time="23:00", admin_id=admin_user.id)
        db.session.add(r)
    return r

# ---------------------- MENUS ----------------------

@pytest.fixture(scope="function")
def menu(restaurant):
    with db.session.begin():
        m = Menu(name="Test Menu", price=10.0, category="Main", restaurant_id=restaurant.id)
        db.session.add(m)
    return m

# ---------------------- TESTS ----------------------

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
    data = {
        'name': 'Updated Dish',
        'price': 15.0,
        'category': 'Dessert'
    }
    response = client.put(f'/menus/{menu.id}', json=data)
    assert response.status_code == 403
    assert 'Missing Authorization Header' not in response.get_data(as_text=True)


def test_delete_menu(client, auth_token, menu):
    response = client.delete(f'/menus/{menu.id}', headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 200
    assert 'Menu item deleted successfully' in response.get_json()['message']


def test_delete_menu_not_found(client, auth_token):
    response = client.delete('/menus/999', headers={'Authorization': f'Bearer {auth_token}'})
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


def test_create_menu_missing_fields(client, auth_token, restaurant):
    data = {
        'name': 'Incomplete Dish',
        'price': 12.0,
        'category': 'Main'
    }
    response = client.post('/menus', json=data, headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 400
    assert 'Missing required field' in response.get_json()['message']


def test_create_menu_restaurant_not_found(client, auth_token):
    data = {
        'name': 'Test Dish',
        'price': 12.0,
        'category': 'Main',
        'restaurant_id': 999
    }
    response = client.post('/menus', json=data, headers={'Authorization': f'Bearer {auth_token}'})
    assert response.status_code == 404
    assert 'Restaurant not found' in response.get_json()['message']
