import pytest
from app.app import create_app
from app.extensions import db, migrate
from app.models.user import User
from app.models.restaurant import Restaurant
from flask_jwt_extended import create_access_token
from flask_migrate import upgrade
from config import TestConfig

@pytest.fixture(scope='session')
def app():
    app = create_app(config_class=TestConfig)
    app.config['TESTING'] = True

    # --- APLICAMOS LAS MIGRACIONES ---
    with app.app_context():
        upgrade()  # <-- ESTA es la diferencia clave

    yield app

    # --- Al finalizar tests ---
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='session')
def db_instance(app):
    return db

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_user(app, db_instance):
    with app.app_context():
        admin = User(
            username="admin",
            email="admin@example.com",
            password="password",
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        return admin

@pytest.fixture
def auth_header(admin_user):
    access_token = create_access_token(identity=admin_user.id)
    return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture
def sample_restaurant(app, db_instance, admin_user):
    with app.app_context():
        restaurant = Restaurant(
            name="Sample Restaurant",
            address="123 Sample St",
            phone="123456789",
            open_time="09:00",
            close_time="21:00",
            admin_id=admin_user.id
        )
        db.session.add(restaurant)
        db.session.commit()
        return restaurant
