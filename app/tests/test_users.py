import json
import unittest
from app import create_app
from app.models import db
from app.models.user import User
from app.models.menu import Menu
from app.models.order import Order
from app.models.restaurant import Restaurant
from app.models.reservation import Reservation
from flask_jwt_extended import create_access_token
from config import TestConfig

class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Crear usuarios de prueba
        self.admin_user = User(username='admin', email='admin@example.com', password=User.generate_hash('password'), role='admin')
        self.admin_user.save_to_db()

        self.client_user = User(username='client', email='client@example.com', password=User.generate_hash('password'), role='client')
        self.client_user.save_to_db()

        # Obtener tokens
        with self.app.test_request_context():
            self.admin_token = create_access_token(identity=self.admin_user.id)
            self.client_token = create_access_token(identity=self.client_user.id)

        # Crear restaurante de prueba
        self.restaurant = Restaurant(name='Test Restaurant', address='123 Test St', phone='123-456', open_time='08:00', close_time='22:00', admin_id=self.admin_user.id)
        self.restaurant.save_to_db()

        # Crear menú de prueba
        self.menu = Menu(name='Test Menu', description='Test Description', price=10.0, category='Main', restaurant_id=self.restaurant.id)
        self.menu.save_to_db()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # ---- TEST USUARIOS ----
    def test_register_user(self):
        response = self.client.post('/auth/register', data=json.dumps({
            'username': 'newuser', 'email': 'new@example.com', 'password': 'password123'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 201)

    def test_login_user(self):
        response = self.client.post('/auth/login', data=json.dumps({'username': 'client', 'password': 'password'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)

    # ---- TEST MENÚS ----
    def test_create_menu(self):
        response = self.client.post('/menus', headers={'Authorization': f'Bearer {self.admin_token}'},
                                    data=json.dumps({'name': 'New Menu', 'price': 15.0, 'category': 'Main', 'restaurant_id': self.restaurant.id}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)

    def test_get_menus(self):
        response = self.client.get(f'/menus/{self.menu.id}')
        self.assertEqual(response.status_code, 200)

    # ---- TEST ÓRDENES ----
    def test_create_order(self):
        response = self.client.post('/orders', headers={'Authorization': f'Bearer {self.client_token}'},
                                    data=json.dumps({'pickup_time': '2025-03-22 12:00', 'restaurant_id': self.restaurant.id, 'items': [{'menu_id': self.menu.id, 'quantity': 2}]}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)

    # ---- TEST RESERVACIONES ----
    def test_create_reservation(self):
        response = self.client.post('/reservations', headers={'Authorization': f'Bearer {self.client_token}'},
                                    data=json.dumps({'date': '2025-03-22', 'time': '19:00', 'guests': 2, 'restaurant_id': self.restaurant.id}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)

if __name__ == '__main__':
    unittest.main()