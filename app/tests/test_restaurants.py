import json
import unittest
from app import create_app
from app.models import db
from app.models.user import User
from app.models.restaurant import Restaurant
from flask_jwt_extended import create_access_token
from config import TestConfig

class RestaurantsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Crea usuarios test
        self.admin_user = User(
            username='admin_user',
            email='admin@example.com',
            password=User.generate_hash('password123'),
            role='admin'
        )
        self.admin_user.save_to_db()

        self.regular_user = User(
            username='regular_user',
            email='regular@example.com',
            password=User.generate_hash('password123'),
            role='client'
        )
        self.regular_user.save_to_db()

        # Obtiene tokens
        with self.app.test_request_context():
            self.admin_token = create_access_token(identity=self.admin_user.id)
            self.user_token = create_access_token(identity=self.regular_user.id)

        # Crea restaurante de t est
        self.test_restaurant = Restaurant(
            name='Test Restaurant',
            address='123 Test St',
            phone='123-456-7890',
            description='Test Description',
            open_time='08:00',
            close_time='22:00',
            admin_id=self.admin_user.id
        )
        self.test_restaurant.save_to_db()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_restaurant(self):
        # Test creando restaurante como admin
        response = self.client.post(
            '/restaurants',
            headers={'Authorization': f'Bearer {self.admin_token}'},
            data=json.dumps({
                'name': 'New Restaurant',
                'address': '456 New St',
                'phone': '987-654-3210',
                'description': 'New Description',
                'open_time': '09:00',
                'close_time': '21:00'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn('Restaurant created successfully', response.get_json()['message'])

        # Test creando restaurante como usuario normal (deberia de fallar)
        response = self.client.post(
            '/restaurants',
            headers={'Authorization': f'Bearer {self.user_token}'},
            data=json.dumps({
                'name': 'Another Restaurant',
                'address': '789 Another St',
                'phone': '555-555-5555',
                'description': 'Another Description',
                'open_time': '10:00',
                'close_time': '20:00'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn('Admin privileges required', response.get_json()['message'])

    def test_get_restaurants(self):
        # Test haciendo get de todos los restaurantes
        response = self.client.get('/restaurants')
        self.assertEqual(response.status_code, 200)
        restaurants = response.get_json()
        self.assertEqual(len(restaurants), 1)
        self.assertEqual(restaurants[0]['name'], 'Test Restaurant')

    def test_get_restaurant(self):
        # Test obteniendo un restaurante especifico
        response = self.client.get(f'/restaurants/{self.test_restaurant.id}')
        self.assertEqual(response.status_code, 200)
        restaurant = response.get_json()
        self.assertEqual(restaurant['name'], 'Test Restaurant')
        self.assertEqual(restaurant['address'], '123 Test St')

        # Test obteniendo restaurantes inexistentes
        response = self.client.get('/restaurants/999')
        self.assertEqual(response.status_code, 404)
        self.assertIn('Restaurant not found', response.get_json()['message'])

    def test_update_restaurant(self):
        # Test actualizando como admin
        response = self.client.put(
            f'/restaurants/{self.test_restaurant.id}',
            headers={'Authorization': f'Bearer {self.admin_token}'},
            data=json.dumps({
                'name': 'Updated Restaurant',
                'description': 'Updated Description'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Restaurant updated successfully', response.get_json()['message'])

        # Verifica la actualizacion
        response = self.client.get(f'/restaurants/{self.test_restaurant.id}')
        restaurant = response.get_json()
        self.assertEqual(restaurant['name'], 'Updated Restaurant')
        self.assertEqual(restaurant['description'], 'Updated Description')

        # Test actualizando como usuario normal (deberia fallar)
        response = self.client.put(
            f'/restaurants/{self.test_restaurant.id}',
            headers={'Authorization': f'Bearer {self.user_token}'},
            data=json.dumps({
                'name': 'User Updated Restaurant'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn('Permission denied', response.get_json()['message'])

    def test_delete_restaurant(self):
        # Test borrando como admin
        response = self.client.delete(
            f'/restaurants/{self.test_restaurant.id}',
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Restaurant deleted successfully', response.get_json()['message'])

        # Verifica el eliminado
        response = self.client.get(f'/restaurants/{self.test_restaurant.id}')
        self.assertEqual(response.status_code, 404)
        self.assertIn('Restaurant not found', response.get_json()['message'])

if __name__ == '__main__':
    unittest.main()